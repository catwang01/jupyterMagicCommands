from typing import Callable, Dict, Optional
from jupyterMagicCommands.session import Session
from jupyterMagicCommands.utils.log import NULL_LOGGER

SessionID = str
SessionDict = Dict[SessionID, Session]
SessionRetriever = Callable[[], Session]

class SessionManager:

    sessions: SessionDict
    
    def __init__(self, sessions: Optional[SessionDict] = None, logger=NULL_LOGGER):
        self.sessions = sessions or {}
        self.logger = logger
    
    def getSession(self, id: SessionID) -> Optional[Session]:
        session = self.sessions.get(id)
        return session

    def getOrCreateSession(self, id: SessionID, retrieveSession: SessionRetriever) -> Session:
        session = self.getSession(id)
        if session is None:
            self.logger.debug("Creating a new session with id %s", id)
            session = retrieveSession()
            self.sessions[id] = session
        else:
            self.logger.debug("Get cached session with id %s", id)
        return session