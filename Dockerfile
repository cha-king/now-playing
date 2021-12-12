FROM node:15.10.0 AS react-builder

WORKDIR /build

COPY ./frontend/package.json ./frontend/yarn.lock ./
RUN npm install

COPY ./frontend/public ./public
COPY ./frontend/src ./src

RUN npm run build


FROM python

WORKDIR /app

COPY ./backend/requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY ./backend/now-playing ./now-playing

COPY --from=react-builder /build/build /app/now-playing/static

CMD ["uvicorn", "now-playing:app", "--host=0.0.0.0"]

EXPOSE 8000
