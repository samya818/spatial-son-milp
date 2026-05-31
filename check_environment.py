"""
Pre-flight environment checker for Spatial SON-MILP.
Verifies Python version, virtual environment, dependencies, and critical files.
"""
import sys
import os
import importlib.util
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_check(name, success, message=""):
    symbol = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
    print(f"{symbol} {name.ljust(30)} {message}")
    return success

def check_python_version():
    is_valid = sys.version_info >= (3, 10)
    return print_check("Python >= 3.10", is_valid, f"(Found {sys.version.split()[0]})")

def check_venv():
    # Detect venv via sys.prefix vs sys.base_prefix
    in_venv = sys.prefix != sys.base_prefix
    return print_check("Virtual Environment", in_venv, "" if in_venv else f"{YELLOW}Please activate your venv!{RESET}")

def check_dependencies():
    critical = [
        "polars", "numpy", "xgboost", "lightgbm", "pyomo", 
        "streamlit", "sklearn", "matplotlib", "plotly", "pytest",
        "psutil", "loguru", "pulp", "pandera"
    ]
    missing = []
    for lib in critical:
        if importlib.util.find_spec(lib) is None:
            # sklearn is actually 'scikit-learn' in pip but 'sklearn' in import
            if lib == "sklearn":
                 if importlib.util.find_spec("sklearn") is None:
                    missing.append(lib)
            else:
                missing.append(lib)
            
    success = len(missing) == 0
    msg = "" if success else f"{RED}Missing: {', '.join(missing)}{RESET}"
    return print_check("Critical Dependencies", success, msg)

def check_solver():
    """Checks if the CBC solver is available for MILP optimization."""
    import shutil
    cbc_path = shutil.which("cbc")
    
    # Also check via pulp fallback
    if not cbc_path:
        try:
            import pulp
            path = pulp.PULP_CBC_CMD().path
            if Path(path).exists():
                cbc_path = path
        except:
            pass
            
    success = cbc_path is not None
    msg = f"{GREEN}(Found at {cbc_path}){RESET}" if success else f"{YELLOW}Warning: CBC solver not found. MILP will fail.{RESET}"
    return print_check("MILP Solver (CBC)", success, msg)

def check_critical_files():
    files = [
        "research/offline/fractions_1024.parquet",
        "research/models/xgb_q80.pkl",
        "research/models/lgbm_l2_corrector.pkl",
        "scripts/dashboard/app.py"
    ]
    missing = [f for f in files if not Path(f).exists()]
    success = len(missing) == 0
    msg = "" if success else f"{RED}Missing: {', '.join(missing)}{RESET}"
    return print_check("Critical Assets", success, msg)

def check_project_structure():
    dirs = ["research/notebooks/", "src/", "tests/", "docs/"]
    missing = [d for d in dirs if not Path(d).exists()]
    success = len(missing) == 0
    msg = "" if success else f"{RED}Missing: {', '.join(missing)}{RESET}"
    return print_check("Project Structure", success, msg)

def main():
    print(f"\n{YELLOW}=== Spatial SON-MILP Environment Check ==={RESET}\n")
    
    results = [
        check_python_version(),
        check_venv(),
        check_dependencies(),
        check_solver(),
        check_critical_files(),
        check_project_structure()
    ]
    
    print("\n" + "="*45)
    if all(results):
        print(f"\n{GREEN}CONGRATULATIONS! Your environment is ready.{RESET}")
        print(f"Run the dashboard with: {YELLOW}python -m streamlit run scripts/dashboard/app.py{RESET}\n")
    else:
        print(f"\n{RED}ERROR: Environment setup incomplete.{RESET}")
        print(f"Please check the {RED}✗{RESET} items above and follow instructions in README.md.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
