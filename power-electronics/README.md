# Power electronics

고조파·전력 계산과 정류기 모델, SPICE 회로 예제.

- `basics/`, `appendix/` — 표준 라이브러리를 쓰는 계산 스크립트
- `rectifiers/pe.py` — 반파·전파·환류·커패시터 필터 모델
- `rectifiers/reproduce_checks.py` — 독립 ODE 해법, 전력·전하 평형 비교
- `netlists/` — PSpice 형식 회로 입력

```sh
pip install numpy scipy
cd rectifiers
python3 reproduce_checks.py
```

계산은 각 예제의 파라미터와 이상화한 모델을 사용합니다. SPICE 예제는 별도 실행 환경이 필요하며, `IRF150_p1_3_template.cir`에는 소자 모델과 핀 순서를 채워야 합니다. ABM 표현식과 `VSWITCH` 지원 여부도 사용하는 시뮬레이터에서 확인하세요.
