### orchestration layer in conversation module

```mermaid
flowchart TD
    A[demo tester response to initial bot Whapp text ] --> B[identify guest via phone lookup];
    B --> C[retrieve current guest state];
    C --> D[retrieve last 3 messages];
    D --> E[conversation service / core app functionality];
    E --> F[construct model input aka feed context to LLM];
    F -- LLM interprets mssg given context ---> G[LLM extracts structured RSVP info];
    G --> H[LLM proposes updates to guest state];
    F --> I[LLM drafts reply];
    H --> J[Pydantic validation];
    J --> K[Deterministic business rules];
    K --> L[update guest state in Guests Sheet aka persistence];
    L --> M[conversation service decides on reply sent];
```


|Definitions        |                                                         |
|:----------------  |:--------------------------------------------------------|
| Guest state       | The current RSVP information per guest stored by app    |
| LLM output        | model's interpretation of the guest's message           |
| Proposed update   | The structured change the LLM suggests 			      |
| Business rules    | Deterministic logic that decides y/n re proposed update |
| Message history   |	append only log of the conversation 			   	  |


## webhook workflow

```mermaid
flowchart LR
    A[demo tester's Whapp] <--> B[Twilio];
    B --> C[ngrok];
    C --> D[FastAPI webhook];
    D --> E[RSVP AI agent];
    E --> B;
```
