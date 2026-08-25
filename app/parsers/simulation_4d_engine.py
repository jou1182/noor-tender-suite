import datetime
from typing import List, Dict, Any

class Simulation4DEngine:
    @staticmethod
    def generate_timeline_snapshots(elements: List[Dict[str, Any]], current_date_iso: str = None) -> Dict[str, Any]:
        """
        Parses IFC Structural element GUIDs and maps them chronologically against 
        P6 Primavera start/finish dates to generate stateful time-step interpolations.
        """
        # Determine the dynamic simulation cursor time
        now = datetime.datetime.fromisoformat(current_date_iso) if current_date_iso else datetime.datetime.utcnow()
        
        snapshots = {}
        for elem in elements:
            guid = elem["guid"]
            start = datetime.datetime.fromisoformat(elem["start_date"])
            finish = datetime.datetime.fromisoformat(elem["finish_date"])
            is_critical = elem.get("is_critical", False)
            delay_days = elem.get("delay_days", 0)
            
            # State Machine Interpolation Logic
            if delay_days > 0 and is_critical and now > start:
                state = "CRITICAL_DELAY"
            elif now < start:
                state = "PLANNED"
            elif start <= now <= finish:
                state = "IN_PROGRESS"
            else:
                state = "COMPLETED"
                
            # Progress calculation for smooth WebGL rendering
            if state == "IN_PROGRESS":
                total_duration = (finish - start).total_seconds()
                elapsed = (now - start).total_seconds()
                progress = min(100, max(0, (elapsed / total_duration) * 100))
            elif state == "COMPLETED":
                progress = 100
            else:
                progress = 0
                
            snapshots[guid] = {
                "state": state,
                "color": Simulation4DEngine._get_color_for_state(state),
                "progress": round(progress, 2)
            }
            
        return {
            "simulation_timestamp": now.isoformat(),
            "element_states": snapshots,
            "total_elements": len(elements)
        }

    @staticmethod
    def _get_color_for_state(state: str) -> str:
        colors = {
            "PLANNED": "#94a3b8",       # Slate
            "IN_PROGRESS": "#3b82f6",   # Blue
            "COMPLETED": "#10b981",     # Emerald
            "CRITICAL_DELAY": "#ef4444" # Red
        }
        return colors.get(state, "#ffffff")
