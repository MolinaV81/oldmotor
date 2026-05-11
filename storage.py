from __future__ import annotations

import os
from typing import Dict, Any
import pandas as pd

DEFAULT_XLSX = os.path.join("data", "records.xlsx")


def ensure_dirs() -> None:
    os.makedirs("data", exist_ok=True)
    os.makedirs("output_pdfs", exist_ok=True)


def append_record(record: Dict[str, Any], xlsx_path: str = DEFAULT_XLSX) -> None:
    """
    Agrega 1 registro al Excel (append). Si no existe, lo crea.
    """
    ensure_dirs()
    df_new = pd.DataFrame([record])

    if os.path.exists(xlsx_path):
        df_old = pd.read_excel(xlsx_path)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_excel(xlsx_path, index=False)


def load_records(xlsx_path: str = DEFAULT_XLSX) -> pd.DataFrame:
    ensure_dirs()
    if not os.path.exists(xlsx_path):
        return pd.DataFrame()
    return pd.read_excel(xlsx_path)
