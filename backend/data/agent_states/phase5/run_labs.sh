#!/bin/bash
# key|univ_th|univ_en|seed urls...
run() { k=$1; th=$2; en=$3; shift 3; args=(); for u in "$@"; do args+=(--url "$u"); done
  PYTHONPATH=backend PYTHONIOENCODING=utf-8 timeout 3000 backend/.venv/Scripts/python.exe backend/scripts/agentic_pipeline/lab_cli_runner.py \
   --univ-th "$th" --univ-en "$en" "${args[@]}" --max-steps 40 \
   --export-file "backend/data/agent_states/phase5/$k.py" > "backend/data/agent_states/phase5/$k.log" 2>&1
  echo "$k done: $(grep -o 'Labs exported: [0-9]*' backend/data/agent_states/phase5/$k.log)"; }
run cu "จุฬาลงกรณ์มหาวิทยาลัย" "Chulalongkorn University" https://www.chula.ac.th/ &
run kmutt "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี" "King Mongkut's University of Technology Thonburi" https://www.kmutt.ac.th/research/research-lab-unit/ https://www.kmutt.ac.th/ &
run kmitl "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง" "King Mongkut's Institute of Technology Ladkrabang" https://kris.kmitl.ac.th/center-of-excellence/ https://www.kmitl.ac.th/ &
wait
run cmu "มหาวิทยาลัยเชียงใหม่" "Chiang Mai University" https://www.cmu.ac.th/ &
run kku "มหาวิทยาลัยขอนแก่น" "Khon Kaen University" https://research.kku.ac.th/ https://www.kku.ac.th/ &
run ku "มหาวิทยาลัยเกษตรศาสตร์" "Kasetsart University" https://www.ku.ac.th/ &
wait
run psu "มหาวิทยาลัยสงขลานครินทร์" "Prince of Songkla University" "https://www.psu.ac.th/?page=research" https://www.psu.ac.th/ &
run tu "มหาวิทยาลัยธรรมศาสตร์" "Thammasat University" https://tu.ac.th/research/ https://tu.ac.th/ &
run sut "มหาวิทยาลัยเทคโนโลยีสุรนารี" "Suranaree University of Technology" https://www.sut.ac.th/ &
wait
