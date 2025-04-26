# TERESA Command Line Interface Tool

## Requirements
- Python3 and pip
- Git
- Docker Engine
    - if you are on MacOS, I strongly recommend installing OrbStack

## Install Instructions
- TODO

## Troubleshooting

### Linux
Docker commands will run assuming you don't need to prefix with `sudo`, so you may need to add your user to the docker group and restart your machine via:
```
sudo usermod -aG docker $USER
sudo restart
```

Additionally, we are assuming that we're using just the plain ol' Docker Engine, not Docker Desktop. To set our docker context to the Docker Engine, do the following:
```
docker context use default
```

