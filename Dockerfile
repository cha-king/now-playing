FROM node:15.10.0 AS react-builder

WORKDIR /build

COPY ./frontend/package.json ./frontend/yarn.lock ./
RUN npm install

COPY ./frontend/public ./public
COPY ./frontend/src ./src

RUN npm run build


FROM python:3.10 as python-builder

WORKDIR /build

COPY ./backend/requirements.txt ./requirements.txt

RUN pip wheel -r requirements.txt -w ./wheels


FROM python:3.10-slim

RUN apt update && apt install -y \
    libjpeg62 \
    libtiff5 \
    libxcb1 \
    libopenjp2-7

COPY --from=python-builder /build /build

WORKDIR /build

COPY ./backend/requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt --no-index --find-links ./wheels/

WORKDIR /app

COPY ./backend/now-playing ./now-playing

COPY --from=react-builder /build/build /app/now-playing/static

CMD ["uvicorn", "now-playing:app", "--host=0.0.0.0", "--proxy-headers"]

EXPOSE 8000
