## // Requirements 
# Refer to RAG_chatbot.ipynb under /jupyter_tutorials for detailed instructions
# pip install langchain langchain_community langchain_chroma
# pip install -qU langchain-openai

## // Imports
import os
import bs4
from dotenv import load_dotenv
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader # Select loader type from https://python.langchain.com/v0.2/docs/integrations/document_loaders/
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI 
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")
'''You can test model with llm.invoke("Your input)'''

## // API Keys
''' Options: Define Langsmith tracing parameters OR you can set env variables'''
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = getpass.getpass()

os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_ENDPOINT'] = "https://api.smith.langchain.com"
os.environ['LANGCHAIN_PROJECT'] = "RAG_for_SQLi"
# Required to set env variable for USER_AGENT in BeautifulSoup 
os.environ['USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'

openai_api_key = os.getenv('OPENAI_API_KEY', 'YourAPIKeyIfNotSet')
langchain_api_key = os.getenv('LANGCHAIN_API_KEY', 'YourAPIKeyIfNotSet') # 5000 free traces per month


# Load, chunk and index the contents of the blog.
loader = WebBaseLoader( #invicti blog content starts from char 2650 - 32270
    web_paths=("https://www.invicti.com/blog/web-security/sql-injection-cheat-sheet/",)
    # USE THE BELOW SECTION FOR FILTERING
    , bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("content")
        )
    ),
)

'''
For loading txt/unstructured files and documents, follow:
https://github.com/hwchase17/chat-your-data/blob/master/ingest_data.py

Inventory of alternate sites:
https://gist.githubusercontent.com/Cuncis/eb6a0857b16e818a069da1e2c7e3f366/raw/170e31eee6da787f287a8e757415142aee3254ed/sql_injection_2021_attacks.txt
Getting started finding a vulnerable parameter: https://github.com/AdmiralGaust/SQL-Injection-cheat-sheet

Master list: https://www.netsparker.com/blog/web-security/sql-injection-cheat-sheet/

General list: https://portswigger.net/web-security/sql-injection/cheat-sheet

UNION attacks: https://portswigger.net/web-security/sql-injection/union-attacks

Info gathering: https://portswigger.net/web-security/sql-injection/examining-the-database

Blind injections: https://portswigger.net/web-security/sql-injection/blind

General SQL tips & tricks: https://sqlzoo.net/

Juice Shop hints: https://bkimminich.gitbooks.io/pwning-owasp-juice-shop/part2/injection.html

Getting started finding a vulnerable parameter
https://github.com/AdmiralGaust/SQL-Injection-cheat-sheet
'''

docs = loader.load()

'''check length of characters'''
# len(docs[0].page_content) 
'''print preview up to 500 char'''
# print(docs[0].page_content[32000:32270]) 

## // Truncating doc content to targeted ones
x = docs[0].page_content[2650:32270]
docs[0].page_content = x
# len(docs[0].page_content)

## // Indexing to split the loaded document
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)

'''Check number of chunks'''
# len(all_splits) 
'''Length of page content'''
# len(all_splits[0].page_content)
'''Check metadata''' 
# all_splits[10].metadata 
# {'source': 'https://www.invicti.com/blog/web-security/sql-injection-cheat-sheet/','start_index': 7163}

## // Indexing
'''
- store the text chunks for search during runtime, embed contents of each doc split and insert embeddings into a vector database
- search will be by cosine similarity between query embeddings and vector database
'''
vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())

## // Retrieval 
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

'''Testing retrieved doc using sample query'''
# retrieved_docs = retriever.invoke("How do I check for MySQL version on a target during SQL injection attacks?")
# len(retrieved_docs)  
# print(retrieved_docs[0].page_content)

## // Generate
# Custom prompt template - https://smith.langchain.com/hub/davincico/rag-pentest-prompt
prompt = hub.pull("davincico/rag-pentest-prompt")

example_messages = prompt.invoke(
    {"context": "filler context", "question": "filler question"}
).to_messages()

# example_messages
# print(example_messages[0].content)

## // LCEL Runnables Protocol
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs , "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

''' # Testing prompt without LLM first
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
)
chain.invoke(question)'''

for chunk in rag_chain.stream("What is an example of MySQL Version Detection Sample Attacks? Give a sample containing only the payload. The attack must be able to tell us if the SQL version is higher than a certain number X.XX"):
    print(chunk, end="", flush=True)


## // Cleanup
# vectorstore.delete_collection()