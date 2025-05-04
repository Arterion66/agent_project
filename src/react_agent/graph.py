"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS, POKEMONTOOLS, QUOTETOOLS, EMAILTOOL
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

    prompt = """You are a Pokémon expert who tells curious facts and interesting facts.
From the above message, generate 2 or 3 interesting and relevant fun facts about the Pokémon 
about the Pokémon mentioned."""

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

async def appointment_manager(state: State) -> Dict[str, List[AIMessage]]:
    configuration = Configuration.from_context()
    
    # Vinculamos el modelo a las herramientas
    model = load_chat_model("fireworks/accounts/fireworks/models/llama-v3p1-405b-instruct").bind_tools(QUOTETOOLS)

    prompt = """You are an appointment manager. You can help with the following tasks:
- Checking available time slots for appointments.
- Creating new appointments.
- Rescheduling appointments.
- Canceling existing appointments.

If the user wants to schedule or reschedule a quote or appointment, you must use the corresponding tool call: schedule_quote or reschedule_quote. Do not respond directly; always use the tool when appropriate.

IMPORTANT: When using `schedule_quote`, you MUST ask for the user's Gmail address and full name if they are not provided in the conversation. DO NOT make up or assume any values. Only proceed once you have confirmed them.

Please ensure that the date format for all appointments is as follows: YYYY-MM-DDTHH:mm:ss.

You should also answer questions about appointment availability and scheduling.

Do not invent data. If you do not have the necessary information, ask the user for it.

When checking the available time, it returns the list of appointments so that the user knows exactly which appointments are available.

The current system time is: {system_time}"""

    system_message = prompt.format(system_time=datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%S"))
    
    # El modelo responderá y puede hacer tool_calls
    response = await model.ainvoke([{"role": "system", "content": system_message}, *state.messages])
    
    # Si estamos en el último paso y aún quiere usar herramientas, termina
    if state.is_last_step and response.tool_calls:
        return {"messages": [AIMessage(id=response.id, content="Sorry, I could not find an answer to your question in the specified number of steps.")]}

    return {"messages": [response]}

def route_appointment_output(state: State) -> Literal["quotetools", "email_sender", "__end__"]:
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(f"Expected AIMessage, but got {type(last_message).__name__}")
    
    tool_calls = last_message.tool_calls or []

    if tool_calls:
        # Verifica si las tool_calls son para QUOTETOOLS o EMAILTOOL
        for call in tool_calls:
            name = call["name"] if isinstance(call, dict) else getattr(call, "name", None)
            if name in {"schedule_quote", "reschedule_quote"}:
                return "quotetools"
            elif name == "send_email":
                return "emailtool"
        return "quotetools"  # default si no reconocemos las herramientas
    
    # Verifica si justo antes hubo una ToolMessage de QUOTETOOLS
    if len(state.messages) >= 2:
        prev_tool_result = state.messages[-2]
        if isinstance(prev_tool_result, ToolMessage):
            # Busca el AIMessage correspondiente antes de eso
            for msg in reversed(state.messages[:-2]):
                if isinstance(msg, AIMessage):
                    for call in msg.tool_calls or []:
                        name = call["name"] if isinstance(call, dict) else getattr(call, "name", None)
                        if name in {"schedule_quote", "reschedule_quote"}:
                            return "email_sender"
                    break

    return "__end__"

import uuid

async def email_sender(state: State) -> Dict[str, List[AIMessage]]:
    # Extraer el correo electrónico
    gmail = None
    for msg in state.messages:
        if isinstance(msg, HumanMessage) and "gmail.com" in msg.content:
            gmail = msg.content.split("gmail.com")[0].split()[-1] + "gmail.com"
            break
    
    if not gmail:
        return {"messages": [AIMessage(content="No se pudo encontrar la dirección de correo electrónico.")]}

    # Forzamos directamente la creación de la tool call
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "send_email",
                    "args": {"gmail": gmail},
                    "id": f"call_{str(uuid.uuid4())}"
                }]
            )
        ]
    }

def route_email_output(state: State) -> Literal["emailtool", "__end__"]:
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        return "__end__"
    
    # Si hay tool_calls, vamos a emailtool, sino terminamos
    return "emailtool" if last_message.tool_calls else "__end__"

# Modificación en el grafo para simplificar el flujo
builder_appointment = StateGraph(State, input=InputState, config_schema=Configuration)

# Añadimos los nodos
builder_appointment.add_node("appointment_manager", appointment_manager)
builder_appointment.add_node("quotetools", ToolNode(QUOTETOOLS))
builder_appointment.add_node("email_sender", email_sender)
builder_appointment.add_node("emailtool", ToolNode(EMAILTOOL))

builder_appointment.add_edge("__start__", "appointment_manager")
builder_appointment.add_conditional_edges("appointment_manager", route_appointment_output)
builder_appointment.add_edge("quotetools", "appointment_manager")
builder_appointment.add_edge("email_sender", "emailtool")  # Siempre va a emailtool después de email_sender
builder_appointment.add_edge("emailtool", "__end__")  # Después de enviar el correo, termina

graph_appointment = builder_appointment.compile(name="AppointmentManager")