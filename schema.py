USER_CREATE = {
    "type": "object",
    "properties": {
        "username": {
            "type": "string"
        },
        "email": {
            "type": "string",
            "pattern": "^([A-zА-я0-9]+)@([a-z]+).(ru|com)$"
        },

        "password": {
            "type": "string",
            "pattern": "^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"
        }
    },
    "required": ["username", "email", "password"]
}
