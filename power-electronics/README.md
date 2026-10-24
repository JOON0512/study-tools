# 전력전자 계산 및 회로 예제

개인 학습 과정에서 작성한 계산 코드와 SPICE 입력 예제입니다. 교재의 문제 번호를 참조하는 파일이 있지만 교재 본문·삽화·스캔이나 상용 소자 라이브러리는 포함하지 않습니다.

- `basics`, `appendix`: 표준 라이브러리로 실행하는 고조파·전력 계산
- `rectifiers/pe.py`: NumPy/SciPy 기반 반파·전파·환류·커패시터 필터 등의 수학 모델
- `rectifiers/reproduce_checks.py`, `results.json`: 수치 결과를 전력·전하 평형과 독립 ODE 해법으로 확인
- `netlists`: PSpice 형태의 회로 입력 16개

```sh
pip install numpy scipy
cd rectifiers
python3 reproduce_checks.py
```

이상화한 모델의 수치 검증과 실제 소자 모델을 사용한 회로 시뮬레이션은 별개입니다. SPICE 파일은 이번 공개 준비 과정에서 시뮬레이터로 실행하지 않았습니다. `IRF150_p1_3_template.cir`는 사용자 환경의 소자 모델과 핀 순서를 채워야 합니다. ABM 표현식과 `VSWITCH` 등은 사용 중인 시뮬레이터의 문법 지원을 확인해야 합니다.

보관된 예제의 파라미터와 가정에 맞춰 만든 코드이며, 입력 전 범위에서 검증한 범용 회로 해석기는 아닙니다.

2026-10-24: `reproduce_checks.py`의 72개 검산이 모두 통과했습니다.
