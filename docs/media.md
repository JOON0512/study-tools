# Media scripts

## Audio

`audio/check_pitch.py SOURCE.wav RENDERED.wav OUTPUT.wav`는 float32 stereo WAV의 -5반음 변환을 확인합니다. 약 3분짜리 입력에 맞춘 분석 구간과 목표 반음이 코드에 고정되어 있어 다른 음원에는 수정이 필요합니다.

`audio/align_reference.py`는 원본과 변환본의 정렬을 비교합니다. 실행 전 코드의 입력 경로를 맞춰 주세요. 두 도구 모두 NumPy가 필요합니다.

## Images

`images/prepare-reading-images.py`는 `key`, `directory`, `files`를 가진 객체 배열을 표준입력으로 받습니다. `READING_OUTPUT_DIR`로 출력 위치를 지정합니다. Pillow가 필요합니다.

## Sprites

`sprites/source-sheets/<id>.png`에 투명한 3×2 시트를 준비합니다. `SPRITE_FONT`와 `SPRITE_FONT_INDEX`로 자막 글꼴을 지정할 수 있습니다.

`package.py`는 프레임 외에 원래 프로젝트의 설명·검수 파일도 필요합니다. 시트와 글꼴, 부속 파일은 직접 준비해야 합니다.
