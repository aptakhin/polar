This document describes chat protocol

Transport is WebSocket (maybe with long polling like SockJS implementation)

Data format is JSON


Message types:

- `text`
Simple text message 

- `prefetch`
Query with text from user device trying to guess user query

- `suggest`
Query some hints for user input

- `voice`
Send voice stream

- `image`
Send image or images

- `video`
Send video stream 

- `file`
Send files 

- `rate`
Rate answers

- `track`
Track clicked links, currently looking web pages and any other.

- `hello`
Greeting message with user credentials and requesting bot identifiers and version

- `system`
Some management commands e.g. switch bot to other version or set some flags for test

---

Some types available for bot:
- `progress` 
Shows progress operations

- `voicetext` 
Shows recognized text progress from user


## Format

Fields `type` and `request_id` are required.
`type` for message type
`request_id` is unique id for every client request

    {
        "type": "hello",
        "request_id": "...",
        ...
    }


## Examples




### hello message

#### request

`token` – jwt-token
`request_id` – unique from client request_id

    {
        "type": "hello",
        "token": "...",
        "bot_id": "...",
        "request_id": "...",
        "session_id": ..."",
        "context": {}
    }
    
    
#### response
    
    {
        "type": "hello",
        "status": "ok",
        "context": {}
    }
    


#### suggest message

#### request

    {
        "type": "suggest",
        "query": "marry crist"
    }
    
    
#### response
    
