# ------ PRICING FROM: https://openai.com/api/pricing/ ------ #

# 4o
COST_PER_MILLION_TOKENS_4o_INPUT = 2.50
COST_PER_MILLION_TOKENS_4o_OUTPUT = 10

# 4o-mini
COST_PER_MILLION_TOKENS_4o_mini_INPUT = 0.150
COST_PER_MILLION_TOKENS_4o_mini_OUTPUT = 0.600

# ------------ #
# DO NOT EDIT BELOW THIS LINE
# ------------ #

# Get cost per token
# 4o
COST_PER_TOKEN_4o_INPUT = 2.50 / 1000000
COST_PER_TOKEN_4o_OUTPUT = 10 / 1000000

# 4o-mini
COST_PER_TOKEN_4o_mini_INPUT = 0.150 / 1000000
COST_PER_TOKEN_4o_mini_OUTPUT = 0.600 / 1000000

# ------ Token counts from estimates ------ #

# --
# ~415 tokens in base promt, ~1215 tokens in grid content, 35 output labels per grid
# details in: https://github.com/paigemoody/visual-scout/issues/7#issuecomment-2724828185
# --
EST_INPUT_TOKEN_COUNT_PER_REQUEST = 1700
EST_OUTPUT_TOKEN_COUNT_PER_REQUEST = 300

# ------ MATH ------ #

COST_PER_REQUEST_4o = (COST_PER_TOKEN_4o_INPUT * EST_INPUT_TOKEN_COUNT_PER_REQUEST) + (
    COST_PER_TOKEN_4o_OUTPUT * EST_OUTPUT_TOKEN_COUNT_PER_REQUEST
)

COST_PER_REQUEST_4o_mini = (
    COST_PER_TOKEN_4o_mini_INPUT * EST_INPUT_TOKEN_COUNT_PER_REQUEST
) + (COST_PER_TOKEN_4o_mini_OUTPUT * EST_OUTPUT_TOKEN_COUNT_PER_REQUEST)
