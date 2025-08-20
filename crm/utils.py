from pathlib import Path
import pandas as pd
from django.conf import settings

DATA_PATH = Path(settings.BASE_DIR) / 'data' / 'visitas.xlsx'

def append_visit_to_excel(row: dict):
    df_new = pd.DataFrame([row])
    for col in df_new.columns:
        if str(col).lower() in ('datahora', 'when'):
            try:
                df_new[col] = pd.to_datetime(df_new[col]).dt.tz_localize(None)
            except Exception:
                pass
    if DATA_PATH.exists():
        try:
            df_old = pd.read_excel(DATA_PATH)
        except Exception:
            df_old = pd.DataFrame()
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(DATA_PATH, index=False)
