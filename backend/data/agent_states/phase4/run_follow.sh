#!/bin/bash
# key|univ_th|univ_en|seed urls...
run() { k=$1; th=$2; en=$3; shift 3; args=(); for u in "$@"; do args+=(--url "$u"); done
  PYTHONPATH=backend PYTHONIOENCODING=utf-8 timeout 3000 backend/.venv/Scripts/python.exe backend/scripts/agentic_pipeline/course_cli_runner.py \
   --univ-th "$th" --univ-en "$en" "${args[@]}" --follow-links --max-steps 40 \
   --export-file "backend/data/agent_states/phase4/$k.py" > "backend/data/agent_states/phase4/$k.log" 2>&1
  echo "$k done: $(grep -c . backend/data/agent_states/phase4/$k.py) lines"; }
run tsu "มหาวิทยาลัยทักษิณ" "Thaksin University" https://www.tsu.ac.th/ &
run wu "มหาวิทยาลัยวลัยลักษณ์" "Walailak University" https://www.wu.ac.th/ &
run buu "มหาวิทยาลัยบูรพา" "Burapha University" https://graduate.buu.ac.th/ https://www.buu.ac.th/ &
run msu "มหาวิทยาลัยมหาสารคาม" "Mahasarakham University" https://www.msu.ac.th/ &
wait
run ubu "มหาวิทยาลัยอุบลราชธานี" "Ubon Ratchathani University" https://www.ubu.ac.th/UBU2025 &
run sut "มหาวิทยาลัยเทคโนโลยีสุรนารี" "Suranaree University of Technology" https://www.sut.ac.th/ &
wait
