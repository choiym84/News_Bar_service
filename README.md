# 📰 News Bar Service

[![Python](https://img.shields.io/badge/Python-3.9-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

## 📌 프로젝트 소개

**News Bar Service**는 현재 이슈가 되는 정치 뉴스를 **진보, 중립, 보수** 정치 성향별로 분류 및 비교하여 제공하는 연구 기반 플랫폼입니다.

---

## ⚠️ 실행 불가 안내

본 프로젝트는 연구 및 결과 공유 목적의 레포지토리이며,  
**정치 성향 분류 모델(kobigbird fine-tuned model)은 라이선스 및 용량 문제로 업로드되어 있지 않습니다.**

따라서 실제 서비스 실행은 불가능하나,  
전체 **데이터 수집 → 키워드 추출 → 정치 성향 분류 → 비교분석 로직** 구조를 확인하실 수 있습니다.

---

## ✨ 주요 기능

- 🔍 네이버 정치 헤드라인 기사 10개 수집
- 🗝️ 현재 이슈 키워드 6개 추출
- 📰 관련 기사 크롤링
- 🏷️ 정치 성향별(진보, 중립, 보수) 기사 분류 *(kobigbird fine-tuned 모델 사용)*
- 📊 정치 성향별 기사 비교 분석 제공
- 🛡️ **가짜뉴스 위험도 판별 알고리즘 적용**
  - 언론사 신뢰도
  - 기사 내 정보 출처의 신뢰도
  - 기사 확산 패턴 (동시다발적 출판 여부)

---

## 🔗 데이터 및 모델 학습 출처

본 프로젝트의 **정치 성향 분류 모델 학습**에는 아래 데이터셋을 활용하였습니다:

- [KoPolitic Benchmark Dataset](https://github.com/Kdavid2355/KoPolitic-Benchmark-Dataset)

---

## 🗂️ 프로젝트 구조

```bash
News_Bar_service/
├── main.py
├── models.py
├── schemas.py
├── crud.py
├── news.py
├── README.md
└── requirements.txt
