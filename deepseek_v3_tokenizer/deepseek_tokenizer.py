import transformers
from prog_params import ProgParams as p

chat_tokenizer_dir = f"{p.program_dir}/deepseek_v3_tokenizer"

tokenizer = transformers.AutoTokenizer.from_pretrained( 
        chat_tokenizer_dir, trust_remote_code=True
        )
