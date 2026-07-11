from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
# from azure.core.credentials import AzureKeyCredential
from autogen_ext.tools.azure import AzureAISearchTool
import asyncio
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
import os
from dotenv import load_dotenv
from autogen_agentchat.teams import SelectorGroupChat
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from azure.identity.aio import ManagedIdentityCredential

load_dotenv()

model = os.environ["MODEL_NAME"]
api_key = os.environ["AZURE_OPENAI_KEY"]  
endpoint = os.environ["AUTOGEN_OPENAI_ENDPOINT"]  
# search_key = os.environ["AZURE_SEARCH_KEY"]
managed_identity_client_id = os.environ["MANAGED_IDENTITY_CLIENT_ID"]
client_id = os.environ.get('AZURE_CLIENT_ID')
identity_endpoint = os.environ.get('IDENTITY_ENDPOINT')
   
if client_id:
    print(f"✅ User-Assigned Managed Identity Active")
    print(f"   Client ID: {client_id}")
else:
    print(f"⚠️  No AZURE_CLIENT_ID found - using System-Assigned or default")
if identity_endpoint:
    print(f"✅ MSI Endpoint Available: {identity_endpoint}")

text_mention_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=2)
termination = text_mention_termination | max_messages_termination
 
client = OpenAIChatCompletionClient(
    model=model,
    base_url=endpoint,
    api_key=api_key,
    api_type="azure",
    model_info={
        "json_output": True,
        "function_calling": True,
        "vision": False,
        "structured_output": False,
        "multiturn": False,
        "family": "GPT_4o"  # Example: GPT_35, GPT_4, GPT_4o, etc.
    }  
)

def load_agents_from_json(json_file="agents.json"):
    """
    Load agents configuration from a JSON file and create AssistantAgent instances with AzureAISearchTool for RAG if all fields are present.
    """
    agents = []
    try:
        with open(json_file, 'r') as f:
            agents_config = json.load(f)
        if isinstance(agents_config, list):
            agent_list = agents_config
        else:
            print("Error: Invalid JSON structure. Expected list of agents.")
            return []
        for config in agent_list:
            agent_name = config.get("agent_name", "TestAgent")
            agent_instruction = config.get("agent_instruction", "You are a helpful assistant.")
            azure_ai_search_endpoint = config.get("azure_ai_search_endpoint", "")
            azure_ai_search_index_obj = config.get("azure_ai_search_index_name", "")
            # Extract string value if it's a dict with 'value' key
            if isinstance(azure_ai_search_index_obj, dict):
                azure_ai_search_index_name = azure_ai_search_index_obj.get("value", "")
            elif isinstance(azure_ai_search_index_obj, str):
                azure_ai_search_index_name = azure_ai_search_index_obj
            else:
                print(f"Warning: Invalid azure_ai_search_index_name type: {type(azure_ai_search_index_obj)}")
            # azure_ai_search_api_key = search_key
            azure_mi_client_id = managed_identity_client_id
            tools = []
            if azure_ai_search_endpoint and azure_ai_search_index_name and azure_mi_client_id:
                try:
                    # Use async managed identity for Azure Search authentication
                    credential = ManagedIdentityCredential(client_id=azure_mi_client_id)
                    
                    # search_service_credential = AzureKeyCredential(azure_ai_search_api_key)
                    azure_search_tool = AzureAISearchTool.create_hybrid_search(
                        name=azure_ai_search_index_name + "_search_tool",
                        endpoint=azure_ai_search_endpoint,
                        index_name=azure_ai_search_index_name,
                        credential=credential,  # Now using managed identity credential
                        vector_fields=["text_vector"],
                        search_fields=["title"],
                        select_fields=["chunk"],
                    )
                    tools = [azure_search_tool]
                    print(f"Creating agent with RAG (managed identity): {agent_name}")
                except Exception as e:
                    print(f"Warning: Failed to create AzureAISearchTool with managed identity for agent {agent_name}: {e}")
            else:
                if not azure_mi_client_id:
                    print(f"Warning: Async managed identity not available for agent {agent_name}")
                print(f"Creating agent without RAG: {agent_name}")
            agent = AssistantAgent(
                name=agent_name,
                model_client=client,
                system_message=agent_instruction,
                tools=tools
            )
            agents.append(agent)
        print(f"Successfully loaded {len(agents)} agents")
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Creating default agent.")
        default_agent = AssistantAgent(
            name="DefaultAgent",
            model_client=client,
            system_message="You are a helpful assistant."
        )
        agents.append(default_agent)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return []
    except Exception as e:
        print(f"Error loading agents: {e}")
        return []
    return agents

agents = load_agents_from_json("agents.json")

print("\nLoaded agents:")
for i, agent in enumerate(agents, 1):
    print(f"{i}. {agent.name}")

if agents:
    group_chat = SelectorGroupChat(
        agents,
        model_client=client,
        allow_repeated_speaker=False,
        termination_condition=termination
    )
else:
    print("No agents loaded. Exiting...")
    exit(1)

async def invoke_agent(user_input: str):
    """
    Invoke the group chat with user input
    """
    try:
        result = await group_chat.run(task=user_input)

        if result.messages:
            response = result.messages[-1].source + " : " + result.messages[-1].content 
            print("Final response:", response)
            return response
        
        return "No response received"
    
    except Exception as e:
        print(f"Error during agent invocation: {e}")
        return f"Error: {str(e)}"


# Pydantic model for request body
class AgentRequest(BaseModel):
    user_input: str = Field(alias="userInput")
    
    model_config = {"populate_by_name": True}
    
class AgentResponse(BaseModel):
    response: str
    status: str

# Create FastAPI router
router = APIRouter()

@router.post("/invoke-agent", response_model=AgentResponse)
async def invoke_agent_endpoint(request: AgentRequest):
    """
    Invoke the multi-agent system with user input
    """
    try:
        if not request.user_input.strip():
            raise HTTPException(status_code=400, detail="User input cannot be empty")
        
        # Call the invoke_agent function with the user input from request
        response = await invoke_agent(request.user_input)
        
        return AgentResponse(
            response=response,
            status="success"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        print(f"Error in invoke_agent_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")