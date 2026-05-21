# Ciallo: An Automated Program Repair Framework Based on Prompt Chaining and Large Language Models

Ciallo is an automated program repair(APR) framework. It means automated program repair framework based on prompt ***c***ha***i***ning ***a***nd ***l***arge ***l***anguage m***o***dels.

## Requirements

- Docker
- Knowledge of using Docker

## Quick Start 🚀
Clone this repository
```
git clone https://github.com/AoXiang-Soar/Ciallo.git
cd Ciallo
```
This repository does not include gumtree-spoon-ast-diff.jar. You need to manually download it in the project's root directory by using 
```
wget https://search.maven.org/remote_content?g=fr.inria.gforge.spoon.labs&a=gumtree-spoon-ast-diff&v=1.100&c=jar-with-dependencies -O gumtree-spoon-ast-diff.jar
```
Rename `user_params.py.template` into `user_params.py`, and **set your api key**. Do not modify other context if you use our Docker image
```
mv user_params.py.template user_params.py
```
Pull our built Docker image, or build a Docker image by using our Dockerfile.
```
docker pull aoxiangsoar/ciallo:latest
# or
docker build .
```
Start a Docker container and mount the project root directory to the `/app` directory in the container. Then run `main.py` in your container
```
# Start a Docker container firstly.
# Then run this in your container.
python main.py
```

The testing framework will use the token count of the prompts. By default, we use the embedding token count of GPT-4o as the benchmark. If you need to use another LLM, modify the `get_token_count()` function in `src/utils.py`.

The `TMP_DIR` could not be `/tmp` or other important system Directories.

The `prog_params.py` contains the default parameters for the analysis.

The resulting plausible patches are stored in `output/defects4j_Ciallo/plausible_patches/`.

The paper to cite is 

```bibtex
@misc{feng2026ciallo,
  author       = {Feng, Junlang and Zhang, Fanlong and Wei, Huaxin and Wang, Ziping and Liu, Jianqi},
  title        = {Ciallo: A Structured Search-Based Framework for Automated Program Repair with Large Language Models},
  year         = {2026},
  howpublished = {Preprint. Source code available at \url{https://github.com/AoXiang-Soar/Ciallo}}
}
```

## Star Us ⭐

If this framework is helpful to you, please give us a free star⭐.