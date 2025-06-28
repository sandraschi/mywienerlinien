# LangChain: Building Applications with LLMs

## Introduction
LangChain is an open-source framework for building applications powered by language models. It provides a standard interface for chains, integrations with other tools, and end-to-end chains for common applications.

## Core Concepts

### 1. Components
- **Models**: Interface with different LLM providers
- **Prompts**: Manage and optimize prompts
- **Memory**: Persist state between chain runs
- **Indexes**: Work with your own data
- **Chains**: Sequences of calls to components
- **Agents**: Use LLMs to determine actions

### 2. Key Features
- **Model Agnostic**: Works with OpenAI, Anthropic, Cohere, and more
- **Extensible**: Add new components easily
- **Production Ready**: Tools for deployment and monitoring

## Getting Started

### Installation
```powershell
# Install with pip
pip install langchain

# With common dependencies
pip install langchain[all]

# Or specific integrations
pip install langchain-openai
```

### Basic Usage
```python
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize the language model
llm = OpenAI(temperature=0.9)

# Create a prompt template
template = "What is a good name for a company that makes {product}?"
prompt = PromptTemplate(
    input_variables=["product"],
    template=template,
)

# Create a chain
chain = LLMChain(llm=llm, prompt=prompt)

# Run the chain
result = chain.run("colorful socks")
print(result)
```

## Core Components

### 1. Models
```python
from langchain_openai import ChatOpenAI
from langchain_community.llms import HuggingFaceHub

# Chat model
chat = ChatOpenAI(temperature=0)

# Local model
local_llm = HuggingFaceHub(
    repo_id="google/flan-t5-base",
    model_kwargs={"temperature":0, "max_length":64}
)
```

### 2. Prompts
```python
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

system_template = "You are a helpful assistant that translates {input_language} to {output_language}."
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

human_template = "{text}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
```

### 3. Memory
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
memory.chat_memory.add_user_message("hi!")
memory.chat_memory.add_ai_message("what's up?")

print(memory.buffer)  # Shows the conversation history
```

### 4. Chains
```python
from langchain.chains import SimpleSequentialChain

# Create two simple chains
first_chain = LLMChain(llm=llm, prompt=prompt1)
second_chain = LLMChain(llm=llm, prompt=prompt2)

# Combine them
overall_chain = SimpleSequentialChain(chains=[first_chain, second_chain], verbose=True)

# Run the chain
overall_chain.run("colorful socks")
```

## Advanced Features

### 1. Agents
```python
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType

# Load tools
tools = load_tools(["serpapi", "llm-math"], llm=llm)

# Initialize agent
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# Run the agent
agent.run("What was the high temperature in SF yesterday? What is that number raised to the .023 power?")
```

### 2. Document Loaders
```python
from langchain.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://www.python.org/about/")
documents = loader.load()
```

### 3. Text Splitting
```python
from langchain.text_splitter import CharacterTextSplitter

text_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

texts = text_splitter.split_documents(documents)
```

## Deployment

### 1. LangServe
```python
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI()
add_routes(app, chain, path="/chain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. LangSmith
```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "<your-api-key>"

# Your existing chains will now be automatically logged
chain.run("Hello, world!")
```

## Best Practices

1. **Prompt Engineering**
   - Be explicit in your instructions
   - Use few-shot examples
   - Experiment with temperature settings

2. **Error Handling**
   - Implement retries with backoff
   - Handle rate limits
   - Validate model outputs

3. **Performance**
   - Cache responses when possible
   - Use streaming for long responses
   - Batch process when appropriate

## Resources
- [LangChain Documentation](https://python.langchain.com/)
- [GitHub Repository](https://github.com/langchain-ai/langchain)
- [LangChain Cookbook](https://github.com/langchain-ai/langchain-cookbook)
