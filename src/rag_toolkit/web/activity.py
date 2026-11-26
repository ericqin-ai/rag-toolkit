"""Bounded session-local activity history; never store configuration or exceptions."""

from datetime import datetime, timedelta, timezone

import streamlit as st


def record_event(kind, summary):
    events = st.session_state.setdefault("activity", [])
    events.append(
        {
            "time": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
            "kind": kind,
            **summary,
        }
    )
    del events[:-20]
