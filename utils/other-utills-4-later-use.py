async def summarize_messages(messages: List[BetaMessageParam]) -> List[BetaMessageParam]:
    if len(messages) <= MAX_SUMMARY_MESSAGES:
        return messages
    original_prompt = messages[0]["content"]
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    summary_prompt = """Please provide a detailed technical summary of this conversation. Include:
    1. All file names and paths mentioned
    2. Directory structures created or modified
    3. Specific actions taken and their outcomes
    4. Any technical decisions or solutions implemented
    5. Current status of the task
    6. Any pending or incomplete items
    7. Code that was written or modified

    Original task prompt for context:
    {original_prompt}

    Conversation to summarize:
    {conversation}"""

    conversation_text = ""
    for msg in messages[1:]:
        role = msg['role'].upper()
        if isinstance(msg['content'], list):
            for block in msg['content']:
                if isinstance(block, dict):
                    if block.get('type') == 'text':
                        conversation_text += f"\n{role}: {block.get('text', '')}"
                    elif block.get('type') == 'tool_result':
                        for item in block.get('content', []):
                            if item.get('type') == 'text':
                                conversation_text += f"\n{role} (Tool Result): {item.get('text', '')}"
        else:
            conversation_text += f"\n{role}: {msg['content']}"
    ic(summary_prompt.format(
                original_prompt=original_prompt,
                conversation=conversation_text
            ))
    response = client.messages.create(
        model=SUMMARY_MODEL,
        max_tokens=MAX_SUMMARY_TOKENS,
        messages=[{
            "role": "user",
            "content": summary_prompt.format(
                original_prompt=original_prompt,
                conversation=conversation_text
            )
        }]
    )
    summary = response.content[0].text
    ic(summary)

    new_messages = [
        messages[0],
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"[CONVERSATION SUMMARY]\n\n{summary}"
                }
            ]
        }
    ]
    return new_messages


def create_journal_entry(*, entry_number: int, messages: List[BetaMessageParam], response: APIResponse, client: Anthropic):
    """Usage:         journal_entry_count = 1
        if os.path.exists(JOURNAL_FILE):
             with open(JOURNAL_FILE, 'r',encoding='utf-8') as f:
                 journal_entry_count = sum(1 for line in f if line.startswith("Entry #")) + 1
        journal_contents = get_journal_contents()
        """
    try:
        user_message = ""
        assistant_response = ""
        for msg in reversed(messages):
            if msg['role'] == 'user':
                user_message = _extract_text_from_content(msg['content'])
            if msg['role'] == 'assistant' and response.content:
                assistant_response = " ".join([block.text for block in response.content if hasattr(block, 'text')])
        if not user_message or not assistant_response:
            ic("Skipping journal entry - missing content")
            return
        journal_prompt = f"Summarize this interaction:\nUser: {user_message}\nAssistant: {assistant_response}"
        haiku_response = client.messages.create(
            model=JOURNAL_MODEL,
            max_tokens=JOURNAL_MAX_TOKENS,
            messages=[{"role": "user", "content": journal_prompt}],
            system=JOURNAL_SYSTEM_PROMPT
        )
        summary = haiku_response.content[0].text.strip()
        if not summary:
            ic("Skipping journal entry - no summary generated")
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        journal_entry = f"\nEntry #{entry_number} - {timestamp}\n{summary}\n-------------------\n"
        os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
        journal_entry = ftfy.fix_text(journal_entry)
        with open(JOURNAL_FILE, 'a', encoding='utf-8') as f:
            f.write(journal_entry)
        ic(f"Created journal entry #{entry_number}")
    except Exception as e:
        ic(f"Error creating journal entry: {str(e)}")
