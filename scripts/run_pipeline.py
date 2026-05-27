import argparse
import sys
from pathlib import Path

# Ajout du root au path pour importer les modules src
sys.path.append(str(Path.cwd()))
from src.simulation.runner import SONSimulator, SimConfig

def main():
    parser = argparse.ArgumentParser(description="SON Pipeline Execution CLI")
    parser.add_argument("--cells", type=int, default=1024, help="Cluster size (1024)")
    parser.add_argument("--policy", type=str, default="dynamic", choices=["static", "dynamic"], help="Simulation policy")
    parser.add_argument("--model", type=str, default="xgb_q80", help="Prediction model name")
    parser.add_argument("--threshold", type=float, default=1.0, help="Congestion threshold")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting SON Pipeline ({args.cells} cells, {args.policy} policy)...")
    
    config = SimConfig(
        policy=args.policy, 
        cells=args.cells, 
        model_name=args.model,
        threshold=args.threshold
    )
    
    sim = SONSimulator(config)
    results = sim.run()
    
    print("\n" + "="*40)
    print("SON PIPELINE EXECUTION SUMMARY")
    print("="*40)
    print(f"Policy            : {results['policy']}")
    print(f"Total Unsatisfied : {results['total_unsatisfied']:.2f} Mo")
    print(f"Decisions Made    : {results['decisions_made']}")
    print("="*40)

if __name__ == "__main__":
    main()
