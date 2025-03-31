# visual-scout (🚧 WIP)

A work-in-progress tool for extracting visual elements (objects and text) from a set of videos, using OpenAI.

## Requirements

Before installing `visual-scout`, ensure your system has:

### 1. **python >= 3.8:**

- To check this run the following and ensure a valid python version is shown: 

```
python3 --version
```

### 2. **FFmpeg and FFprobe**: 

- These command-line tools are required for:
    - Extracting frames from videos (ffmpeg)
    - Inspecting video metadata like duration (ffprobe)

- Install on MacOS (using Homebrew):

```
brew install ffmpeg
```

- Or, Install on Ubuntu/Debian:

```
sudo apt update
sudo apt install ffmpeg
```

### 3. **pipx**

_Note:_ pipx is a tool for installing and running Python applications in isolated environments. It ensures that each CLI tool has its own clean environment, separate from your global Python packages. Once installed with pipx, you can run the CLI from anywhere on your computer, just like a native system command.

#### Option 1 - Basic install:

```
python3 -m pip install --user pipx

# Confirm install and add the installed scripts to your shell's PATH:
python3 -m pipx ensurepath
```

#### Option 2 - Install with Homebrew:

```
brew install pipx

# Confirm install and add the installed scripts to your shell's PATH:
pipx ensurepath
```

**Open a new terminal window to ensure all install changes take effect.**

## **Install `visual-scout`**

###  1. Install package from github source

_Note: Eventually, Visual Scout will be published to PyPI._

- The install command will:
    - Clone the Visual Scout repository from GitHub
    -  Install it into an isolated virtual environment
    - Make the visual-scout command available globally on your system

#### Option 1 - Basic install

```
python3 -m pipx install git+https://github.com/paigemoody/visual-scout.git
```

#### Option 2 - Use Homebrew

```
pipx install git+https://github.com/paigemoody/visual-scout.git
```


### 4. **Verify installation**

```
visual-scout --help
```

# Process Video

Note: This process is still under construction - for now there are four processes that must be run sequentially to generate output data.

## Estimate Cost

This is a _rough_ estimate based on napkin math of processing cost. For more details on how this works see the write up issue: https://github.com/paigemoody/visual-scout/issues/7.

1. Estimate cost to process all videos, gifs and images in a given input dir

    ```
    visual-scout estimate-cost <path to your input dir>
    ```

    To use example files run: 
    ```
    visual-scout estimate-cost visual_scout/example_input
    ```


## Extract Frames 

This process will extract frames from each video in the given directory. Frame images are extracted at 2 second intervals, and written to the `output_frames` directory.

1. Create a directory and add all the videos you want to process into the new directory (skip this step if you want to use example videos)

2. Extract frames

```visual-scout extract-frames <your directory path>```

To use example videos run: 

```visual-scout extract-frames visual_scout/example_input```

## Generate Grids 

This process will combine extracted frames into sequential image grids, defaulting to 3x3 grids. Grid images are written to a newly created directory called `outputs/`, in a sub directory called `output_grids/`. 

Note: you may want to play around with grid size to figure out the ideal level of detail required for the specific AI model you're using to extract data from the images.

1. Generate grids

    To use default grid size run: 
    
    ```visual-scout generate-grids`

    To use a different grid size run: 
    
    ```visual-scout generate-grids --grid-size <grid size intger>` 

    For example: ```visual-scout generate-grids --grid-size <grid size intger>`

## Extract Visual Content

This is where you will use an AI model (just OpenAI is available for now) to extact information about the visual elements of your videos.

1. Create your .env file

    ```
    cp .env.example .env
    ```

2. Generate an OpenAI API key (skip this if you alredy have one!)

    - [Create an OpenAI account](https://auth.openai.com/authorize?audience=https%3A%2F%2Fapi.openai.com%2Fv1&auth0Client=eyJuYW1lIjoiYXV0aDAtc3BhLWpzIiwidmVyc2lvbiI6IjEuMjEuMCJ9&client_id=DRivsnm2Mu42T3KOpqdtwB3NYviHYzwD&device_id=f2886c79-14d0-49c3-8362-82b93d29b456&ext-login-allow-phone=true&ext-use-new-phone-ui=true&issuer=https%3A%2F%2Fauth.openai.com&max_age=0&nonce=cVdJRWJfTzlSSkp0MU8yRTFPRU8xR0FnVWJlRVZzNlRBTGFORGNicXZXSQ%3D%3D&redirect_uri=https%3A%2F%2Fplatform.openai.com%2Fauth%2Fcallback&response_mode=query&response_type=code&scope=openid+profile+email+offline_access&screen_hint=signup&state=QUoxbTZOcHFxdFJ6LkZNX3dvOEtDQ2VyZ3JNbS5iUHYxN2dsdnFYQ21hQQ%3D%3D&flow=treatment) 
    - [Generate a new API key](https://platform.openai.com/api-keys)
    - Save API key in your `.env` file as your `OPENAI_KEY` 

3. Determine [which model](https://platform.openai.com/docs/models) you want to use and update your .env to reflect your choice. 

    - I'd reccomend starting with `gpt-4o-mini` because it works reasonably well and is significantly cheaper (especially important if you'll be processing a lot of videos!). 
    - Save model choice in your `.env` file as `OPENAI_MODEL` 
    - Add env to your session by running `source .env` 

4. Extract visual content using the CLI by running: 

```
visual-scout generate-labels --open-ai-key=$OPENAI_KEY
``` 

    - Add optional additional arg `--open-ai-model` if you want to specify a model. The default is `gpt-4o-mini`
    - This will send the grids produced in the previous step to OpenAI along with a prompt which asks it to return a json object containing everything it sees in the video. 
    - The output is:
        - An individual json file containing the visual elements for one individual grid file, and 
        - One large json file that combines all the individual json files into one, associating each group of elements to their corresponding timestamp. 


## Development Setup

The following is only necessary if you are making changes to the underlying package logic.

1. Create virtual environment

```
python3 -m venv venv
```

2. Activate virtual environment

```
source venv/bin/activate
```

3. Install visual scout in editable mode

```
pipx install -e .
```

4. Confirm installation

```
visual-scout --help
```

5. Run tests

```
pytest
```