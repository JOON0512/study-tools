# Study & creative workflow tools

개인 학습·영상·이미지 작업에서 사용한 작은 Python 도구를 모았습니다. 코드와 비민감 계산 예제만 포함합니다. 원본 음원, 읽기 자료, 캐릭터 원화, 개인 대화와 보고서는 포함하지 않습니다.

| 폴더 | 내용 | 실행 조건 |
|---|---|---|
| `power-electronics/` | 회로 해석의 고조파·RMS·유효전력 계산 | 기본 계산: 표준 라이브러리 / 정류기: NumPy·SciPy |
| `audio/` | float32 stereo WAV의 정렬과 피치 변환 검증 | NumPy, 사용자가 준비한 WAV |
| `images/` | 이미지 배열을 이어 읽기용 조각으로 저장 | Pillow, JSON 입력 |
| `sprites/` | 3×2 원화 시트에서 프레임·자막·WebP 생성 및 규격 확인 | Pillow, 직접 준비한 원화·글꼴 |

```sh
python3 power-electronics/basics/calculate.py
python3 power-electronics/appendix/calculate.py
```

계산 결과는 각 스크립트 옆 `data.json`에 저장됩니다. 포함된 숫자는 특정 회로 실습의 예제이며 일반 회로의 해석 결과로 사용하면 안 됩니다.

읽기용 이미지 도구는 `key`, `directory`, `files`를 가진 객체 배열을 표준입력으로 받습니다. 출력 위치는 `READING_OUTPUT_DIR`로 설정합니다. 예:

```sh
printf '%s' '[{"key":"sample","directory":"./my-images","files":["01.png","02.png"]}]' |
  python3 images/prepare-reading-images.py
```

`audio/check_pitch.py SOURCE.wav RENDERED.wav OUTPUT.wav`는 원래 약 3분 분량 영상의 **-5반음 변환 검수**를 위해 만든 스크립트입니다. 분석 구간과 목표 반음이 코드에 고정돼 있으므로 다른 길이·목표에 적용하려면 수정해야 합니다. `align_reference.py`의 기본 입력 위치도 예제로 남아 있습니다. 범용 음원 편집기로 완성된 프로그램은 아닙니다.

스프라이트 도구는 `sprites/source-sheets/<id>.png`에 투명한 3×2 시트를 두고 실행합니다. 원화와 포즈 생성은 별도 작업입니다. `SPRITE_FONT`와 `SPRITE_FONT_INDEX`로 글꼴을 바꿀 수 있습니다. `package.py`는 원래 프로젝트의 검수·설명 파일까지 모으는 보관용 코드이며, 코드만 받은 상태에서는 패키지 전체를 생성할 수 없습니다. 파일 규격 검사는 플랫폼의 심사 승인을 뜻하지 않습니다.

2026-10-24: 모든 Python 파일 구문 검사와 두 회로 계산 스크립트 실행을 확인했습니다. 원본 미디어가 필요한 전체 제작 흐름은 이 공개 복사본에서 재검증하지 않았습니다.

추가한 정류기 모델은 2026-10-24에 독립 ODE·전력/전하 평형 등을 확인하는 72개 검산을 통과했습니다. SPICE 입력 16개는 실행 전 예제입니다. 자세한 범위는 [전력전자 설명](power-electronics/README.md)에 있습니다. 스프라이트 예제의 인명·대화 참조는 제거하고 문구를 일반 예제로 바꿨습니다.
