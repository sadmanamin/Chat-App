# Chat-App

Clone the repository

```git clone git@github.com:sadmanamin/Chat-App.git```

Go to current directory

```cd Chat-App```

Start docker containers of Server

```
cd Server
docker-compose up --build
cd ..
```


Build Client

```docker build -t client ./Client```

Run each client using the following command

```docker run --network=host -ti client```
