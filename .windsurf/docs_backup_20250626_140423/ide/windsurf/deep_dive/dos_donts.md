# Windsurf IDE: The Do's and Don'ts

## Best Practices for Agentic Collaboration

Working effectively with an agentic AI like Cascade requires a new set of habits. Following these best practices will help you avoid common frustrations and build a more productive partnership with your AI assistant. This guide outlines the key "Do's" to embrace and "Don'ts" to avoid for a smooth and efficient workflow.

--- 

## What You Should Do

### ✅ Do: Be Clear and Specific in Your Goals
Provide the agent with a clear, well-defined objective. The more specific you are about the desired *outcome*, the better the agent can plan and execute the task. Think about what success looks like and describe it.

-   **Example**: "**Do** create a REST API endpoint at `/users/{user_id}` that retrieves a user's data from the database and returns it as JSON. It should handle cases where the user is not found by returning a 404 error."

### ✅ Do: Trust, but Verify
Treat the agent as a talented but junior developer. Trust it to handle the implementation, but always review the code it produces. The agent is a powerful tool, but you are still the senior partner responsible for the final quality of the codebase. A quick review of the agent's changes can catch subtle misunderstandings before they become bigger issues.

### ✅ Do: Use Iterative Refinement
For complex features, build them up in stages. Start with a high-level request to get the basic structure in place, and then provide a series of smaller, more focused requests to add details and functionality. This keeps you in control of the development process and makes it easier to course-correct if the agent misunderstands a requirement.

### ✅ Do: Leverage the Agent's Research Capabilities
Use the agent as your first stop for research. Ask it to investigate libraries, compare different implementation strategies, or explain complex error messages. This keeps you in the flow of development and saves you the time of context-switching to a web browser.

-   **Example**: "**Do** research the best Python libraries for creating PDF reports. Compare the features of ReportLab and FPDF, and provide a recommendation based on ease of use and flexibility."

### ✅ Do: Proactively Manage Context
Help the agent by ensuring it has the right context. Keep relevant files open in the editor, and explicitly tell it to remember important decisions or project standards. The more context the agent has, the more helpful and accurate its assistance will be.

--- 

## What You Should Avoid

### ❌ Don't: Be Vague or Ambiguous
Avoid overly broad or unclear requests. The agent cannot read your mind, and a vague prompt will lead to a vague or incorrect implementation. This is the most common source of frustration.

-   **Example**: "**Don't** just say 'make the user profile page better.' Instead, be specific: 'Improve the user profile page by organizing the information into tabbed sections for 'Profile', 'Security', and 'Notifications'.'"

### ❌ Don't: Micromanage the Agent
Resist the urge to give the agent a series of tiny, step-by-step instructions that you could have typed yourself. This defeats the purpose of the agentic paradigm. Trust the agent to handle the low-level details.

-   **Example**: "**Don't** tell the agent to 'type `import os`' then 'type `import sys`'. Instead, give it the higher-level task that requires those imports, and it will add them itself."

### ❌ Don't: Blindly Accept All Changes
Never blindly accept the code the agent writes without reviewing it. Always take a moment to understand the changes and ensure they align with the project's goals and your quality standards. You are the ultimate gatekeeper of what gets committed to your codebase.

### ❌ Don't: Assume It Knows Everything
While the agent has access to a vast amount of information, its knowledge is not infallible or universally up-to-date. For highly specialized, niche, or very recent technologies, its knowledge may be incomplete. Always treat its output as a well-informed suggestion, not as absolute fact.

### ❌ Don't: Fight the Agent
If the agent is consistently misunderstanding a request, take a step back. Re-read your prompt and consider how it could be misinterpreted. Often, rephrasing the goal from a different perspective or providing a small example of what you want can resolve the confusion. Fighting it with the same prompt repeatedly will likely lead to the same result.
