# frontend

Once upon a time 웹 화면 · React + TypeScript + Vite + React Router + Tailwind CSS

## 구조
```
frontend/
├─ src/
│  ├─ main.tsx             시작점: React를 화면에 붙이고 라우터 연결
│  ├─ App.tsx              주소(URL)별 화면 목록 (라우팅)
│  ├─ index.css            Tailwind 불러오기
│  └─ pages/               화면 단위 컴포넌트
│     ├─ HomePage.tsx      첫 화면 (서버 연결 상태 표시)
│     └─ NotFoundPage.tsx  없는 주소
├─ index.html              HTML 뼈대
├─ vite.config.ts          Vite 설정 (Tailwind, /api·/auth → 백엔드 프록시)
├─ package.json            실행 스크립트 + 패키지 목록
├─ package-lock.json       설치된 패키지의 정확한 버전
├─ tsconfig*.json          TypeScript 설정
└─ .oxlintrc.json          코드 검사(oxlint) 설정
```

## 실행
1. 패키지 설치: `npm install`
2. 백엔드 서버 실행 ([backend](../backend/README.md))
3. 개발 서버: `npm run dev` → http://localhost:5173

## 빌드 · 코드 검사
- 빌드 (타입 검사 포함): `npm run build`
- 코드 검사: `npm run lint`
