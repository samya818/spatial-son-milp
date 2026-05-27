import numpy as np
import pandas as pd
import polars as pl
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import HistGradientBoostingRegressor
import pmdarima as pm
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

root = Path(r'c:\Users\hp\OneDrive\Desktop\projectTimeSeries')
reports = root / 'reports'
reports.mkdir(parents=True, exist_ok=True)

df = pl.read_parquet(root / 'data' / 'processed' / 'features_target_600cells.parquet').sort(['square_id','slot_30m'])
raw_min = pl.read_parquet(root / 'data' / 'processed' / 'work_600cells.parquet').select(pl.col('slot_30m').min()).item()
df = df.with_columns((((pl.col('slot_30m') - raw_min)//86400)+1).cast(pl.Int32).alias('day_idx'))

cells = sorted(df['square_id'].unique().to_list())[:20]
df = df.filter(pl.col('square_id').is_in(cells))

def fr(d0,d1):
    return df.filter((pl.col('day_idx')>=d0)&(pl.col('day_idx')<=d1))

def metrics(y,yh):
    return float(mean_absolute_error(y,yh)), float(np.sqrt(mean_squared_error(y,yh)))

folds=[('fold_1',(1,35),(36,42)),('fold_2',(1,42),(43,49)),('fold_3',(1,49),(50,56)),('final_test',(1,56),(57,62))]
rows=[]

# baselines
for name,tr,ev in folds:
    e=fr(*ev).with_columns([
        pl.col('internet_volume').alias('b_simple'),
        pl.col('internet_volume').shift(46).over('square_id').alias('b_seasonal'),
        pl.col('roll_mean_24h').alias('b_ma24h')
    ])
    for c,mn in [('b_simple','baseline_simple'),('b_seasonal','baseline_seasonal'),('b_ma24h','baseline_ma24h')]:
        t=e.filter(pl.col(c).is_not_null())
        if t.height==0: continue
        mae,rmse=metrics(t['target_1h'].to_numpy(), t[c].to_numpy())
        rows.append([name,mn,t.height,mae,rmse])

# SARIMA final test only
tr=fr(1,56); te=fr(57,62)
s_preds=[]
for cid in cells:
    ytr = tr.filter(pl.col('square_id')==cid).sort('slot_30m')['internet_volume'].to_numpy()[-(7*48):]
    yte_df = te.filter(pl.col('square_id')==cid).sort('slot_30m')
    yte = yte_df['target_1h'].to_numpy()
    if len(ytr)<200 or len(yte)==0: continue
    try:
        m=pm.auto_arima(ytr,seasonal=True,m=48,d=0,D=1,start_p=0,start_q=0,max_p=1,max_q=1,max_P=1,max_Q=0,stepwise=True,suppress_warnings=True,error_action='ignore',trace=False,maxiter=20)
        yp=m.predict(n_periods=len(yte))
        s_preds.append((yte,yp))
    except Exception:
        pass
if s_preds:
    y=np.concatenate([a for a,b in s_preds]); yp=np.concatenate([b for a,b in s_preds])
    mae,rmse=metrics(y,yp); rows.append(['final_test','sarima_auto_arima_m48',len(y),mae,rmse])

# boosting (hist gbdt) all folds on subset
feature_cols=[c for c in df.columns if c not in {'target_1h','square_id','slot_30m','day_idx'}]
for name,trd,evd in folds:
    trdf=fr(*trd); evdf=fr(*evd)
    trnp=trdf.select(feature_cols+['target_1h']).to_numpy().astype(np.float32)
    evnp=evdf.select(feature_cols+['target_1h']).to_numpy().astype(np.float32)
    Xtr,ytr=trnp[:,:-1],trnp[:,-1]
    Xev,yev=evnp[:,:-1],evnp[:,-1]
    model=HistGradientBoostingRegressor(loss='absolute_error',max_depth=6,learning_rate=0.06,max_iter=120,random_state=42)
    model.fit(Xtr,ytr)
    yp=model.predict(Xev)
    mae,rmse=metrics(yev,yp)
    rows.append([name,'boosting_hist_gbdt',len(yev),mae,rmse])

# LSTM all folds on subset
class LSTM(nn.Module):
    def __init__(self, inp):
        super().__init__(); self.l=nn.LSTM(inp,64,2,batch_first=True,dropout=0.2); self.f=nn.Linear(64,1)
    def forward(self,x):
        o,_=self.l(x); return self.f(o[:,-1,:]).squeeze(-1)

in_cols=['internet_volume','sin_hour','cos_hour','sin_dow','cos_dow','is_weekend']
seq=48

def mk(data):
    X,Y=[],[]
    for cid in cells:
        c=data.filter(pl.col('square_id')==cid).sort('slot_30m')
        ax=c.select(in_cols).to_numpy(); ay=c['target_1h'].to_numpy()
        for i in range(seq,len(c)):
            X.append(ax[i-seq:i]); Y.append(ay[i])
    if not X: return None,None
    return np.asarray(X,np.float32), np.asarray(Y,np.float32)

for name,trd,evd in folds:
    trX,trY=mk(fr(*trd)); evX,evY=mk(fr(*evd))
    if trX is None or evX is None: continue
    mu=trX.mean((0,1),keepdims=True); sd=trX.std((0,1),keepdims=True)+1e-6
    trX=(trX-mu)/sd; evX=(evX-mu)/sd
    ds=TensorDataset(torch.from_numpy(trX), torch.from_numpy(trY))
    dl=DataLoader(ds,batch_size=256,shuffle=True)
    net=LSTM(trX.shape[2]); opt=torch.optim.Adam(net.parameters(),lr=1e-3); loss=nn.L1Loss()
    net.train()
    for _ in range(2):
        for xb,yb in dl:
            opt.zero_grad(); p=net(xb); l=loss(p,yb); l.backward(); opt.step()
    net.eval();
    with torch.no_grad(): yp=net(torch.from_numpy(evX)).numpy()
    mae,rmse=metrics(evY,yp)
    rows.append([name,'lstm_pytorch_seq48',len(evY),mae,rmse])

res=pd.DataFrame(rows,columns=['split','model','n_samples','MAE','RMSE'])
best=(res[res.model.str.startswith('baseline_')].groupby('split',as_index=False)['MAE'].min().rename(columns={'MAE':'MAE_best_baseline'}))
res=res.merge(best,on='split',how='left')
res['skill_vs_best_baseline']=1-(res['MAE']/res['MAE_best_baseline'])
res=res.sort_values(['split','MAE'])
res.to_csv(reports/'metrics_modelling.csv',index=False)
print(res)
print('saved', reports/'metrics_modelling.csv')
