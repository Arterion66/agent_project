"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS, POKEMONTOOLS, GOOGLE_CALENDAR_TOOLS
from react_agent.utils import load_chat_model

# Define the function that calls the model


async def call_model(state: State) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_context()

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model("fireworks/accounts/fireworks/models/llama-v3p1-405b-instruct").bind_tools(TOOLS) # configuration.model

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=UTC).isoformat()
    )

    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages]
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response]}

async def pokemon_expert(state: State) -> Dict[str, List[AIMessage]]:
    configuration = Configuration.from_context()
    model = load_chat_model("fireworks/accounts/fireworks/models/llama-v3p1-405b-instruct").bind_tools(POKEMONTOOLS)
    pokemon_prompt = """You are a helpful AI assistant.
System time: {system_time}

Your job is to provide responses about Pokémon. When you receive a name such as raichu alola or raichu de alola, or any compound names, they should be written with a hyphen, like raichu-alola.
Make sure to add a hyphen to compound names."""
    system_message = pokemon_prompt.format(system_time=datetime.now(tz=UTC).isoformat()) #configuration.system_prompt.format(system_time=datetime.now(tz=UTC).isoformat())

    
    response = cast(AIMessage, await model.ainvoke([{"role": "system", "content": system_message}, *state.messages]))
    
    if state.is_last_step and response.tool_calls:
        return {"messages": [AIMessage(id=response.id, content="Sorry, I could not find an answer to your question in the specified number of steps.")]}
    
    return {"messages": [response]}

# Define a new graph

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(call_model)
builder.add_node("tools", ToolNode(TOOLS))

# Set the entrypoint as `call_model`
# This means that this node is the first one called
builder.add_edge("__start__", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"

def route_model_output_pokemon(state: State) -> Literal["__end__", "pokemon_tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "pokemon_tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "pokemon_tools"

# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    # After call_model finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
graph = builder.compile(name="ReAct Agent")

async def fun_facts_pokemon(state: State) -> Dict[str, List[AIMessage]]:
    configuration = Configuration.from_context()
    model = load_chat_model("fireworks/accounts/fireworks/models/llama-v3p1-405b-instruct")

    prompt = """Eres un experto en Pokémon que cuenta datos curiosos y hechos interesantes.
A partir del mensaje anterior, genera 2 o 3 datos curiosos interesantes y relevantes 
sobre el Pokémon mencionado."""

    system_message = prompt + f"\nHora del sistema: {datetime.now(tz=UTC).isoformat()}"
    response = await model.ainvoke([{"role": "system", "content": system_message}, *state.messages])
    return {"messages": [response]}

def route_output_pokemon(state: State) -> Literal["pokemon_tools", "fun_facts", "__end__"]:
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError("Expected AIMessage")

    # Si el modelo ha dado la información correcta o si no se necesita más interacción
    if last_message.tool_calls:
        return "pokemon_tools"  # Si se necesita más información, vamos al experto
    elif len(state.messages) > 1:
        return "fun_facts"  # Si ya se pasó por el experto, mostramos datos curiosos
    else:
        return "__end__"  # Terminamos el proceso si ya no se necesita más

builder_pokemon = StateGraph(State, input=InputState, config_schema=Configuration)

# Añadimos los nodos necesarios
builder_pokemon.add_node("pokemon_expert", pokemon_expert)
builder_pokemon.add_node("pokemon_tools", ToolNode(POKEMONTOOLS))
builder_pokemon.add_node("fun_facts", fun_facts_pokemon)

# Añadimos los edges para definir el flujo
builder_pokemon.add_edge("__start__", "pokemon_expert")
builder_pokemon.add_conditional_edges("pokemon_expert", route_output_pokemon)
builder_pokemon.add_edge("pokemon_tools", "pokemon_expert")  # Volver al modelo si se necesita más
builder_pokemon.add_edge("fun_facts", "__end__")  # Finalizamos después de mostrar los datos curiosos


graph_pokemon = builder_pokemon.compile(name="PokemonExpert")

