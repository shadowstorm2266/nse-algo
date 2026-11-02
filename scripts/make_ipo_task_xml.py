"""Write the Windows Task Scheduler definition for scripts/record_ipo_live.py. Creates no
task: the owner runs schtasks with the file (commands in docs/data.md, "Live IPO recorder").

    uv run python scripts/make_ipo_task_xml.py [--start YYYY-MM-DD] [--out PATH]

schtasks' own flags cannot set "wake the computer to run this task", so the task is
created from XML (schtasks /Create /XML). One task, three weekly triggers, Monday to
Friday at 12:00, 15:30 and 19:30 IST; the +05:30 offset keeps them on IST whatever the PC's
time zone. The script itself skips weekdays listed in config/holidays.csv. Settings:
wake to run; start as soon as possible after a missed start (the run is logged as late);
run on battery; at most 30 minutes; a new start is ignored while one is running; runs only
while the user is logged on (no stored password). Written UTF-16 with a BOM, the encoding
Task Scheduler exports.
"""

import argparse
import os
import shutil
from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape

from nsealgo.data.calendar import IST
from nsealgo.data.live_schedule import SLOT_TIMES
from nsealgo.settings import REPO_ROOT

DEFAULT_OUT = REPO_ROOT / "data" / "live" / "ipo" / "record_ipo_live_task.xml"
DAYS = "<Monday /><Tuesday /><Wednesday /><Thursday /><Friday />"


def trigger(when: datetime) -> str:
    return f"""    <CalendarTrigger>
      <StartBoundary>{when.isoformat()}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek>{DAYS}</DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>"""


def task_xml(start: date, uv: str, repo: Path, user: str) -> str:
    triggers = "\n".join(trigger(datetime.combine(start, t, tzinfo=IST)) for t in SLOT_TIMES)
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>nse-algo IPO track step 3: record NSE live IPO data (data only; no orders, \
no strategy). 12:00, 15:30, 19:30 IST, Mon-Fri; the script skips holidays in \
config/holidays.csv.</Description>
  </RegistrationInfo>
  <Triggers>
{triggers}
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{escape(user)}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{escape(uv)}</Command>
      <Arguments>run python scripts/record_ipo_live.py --scheduled</Arguments>
      <WorkingDirectory>{escape(str(repo))}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", type=date.fromisoformat, default=datetime.now(IST).date())
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv is not on PATH")
    user = f"{os.environ['USERDOMAIN']}\\{os.environ['USERNAME']}"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(task_xml(args.start, uv, REPO_ROOT, user), encoding="utf-16")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
