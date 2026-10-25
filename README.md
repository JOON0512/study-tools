# study-tools

공부하거나 미디어 작업을 하면서 쓴 Python 스크립트 모음.

| 폴더 | 내용 | 의존성 |
| --- | --- | --- |
| [power-electronics](power-electronics) | 고조파, RMS, 전력, 정류기 계산과 SPICE 예제 | 표준 라이브러리, NumPy, SciPy |
| [audio](audio) | WAV 정렬과 피치 변환 확인 | NumPy |
| [images](images) | 여러 이미지를 읽기 편한 조각으로 합치기 | Pillow |
| [sprites](sprites) | 3×2 시트에서 애니메이션 프레임과 WebP 만들기 | Pillow |

회로 계산 예제:

```sh
python3 power-electronics/basics/calculate.py
python3 power-electronics/appendix/calculate.py
```

결과는 각 스크립트 옆 `data.json`에 저장됩니다. 모델과 정류기 계산은 [전력전자 노트](power-electronics/README.md)를 참고하세요.

이미지 합치기:

```sh
printf '%s' '[{"key":"sample","directory":"./my-images","files":["01.png","02.png"]}]' |
  python3 images/prepare-reading-images.py
```

출력 위치는 `READING_OUTPUT_DIR`로 지정합니다. 음원·이미지 입력과 스프라이트 시트 규격은 [미디어 도구 사용법](docs/media.md)에 있습니다.
