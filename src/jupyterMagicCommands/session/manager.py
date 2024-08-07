from typing import Callable, Dict, Optional
from jupyterMagicCommands.session import Session

SessionID = str
SessionDict = Dict[SessionID, Session]
SessionRetriever = Callable[[], Session]

class SessionManager:

    sessions: SessionDict
    
    def __init__(self, sessions: Optional[SessionDict] = None):
        self.sessions = sessions or {}
    
    def getSession(self, id: SessionID) -> Optional[Session]:
        session = self.sessions.get(id)
        return session

    def getOrCreateSession(self, id: SessionID, retrieveSession: SessionRetriever) -> Session:
        session = self.getSession(id)
        if session is None:
            session = retrieveSession()
            self.sessions[id] = session
        return session