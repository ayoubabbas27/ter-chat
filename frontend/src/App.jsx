import { useCallback, useEffect, useRef, useState } from "react";
import {
  checkHealth,
  createSession,
  deleteSession,
  getSession,
  listSessions,
  runGorgiasQuery,
  streamChat,
  updateSession,
  validateSyntaxStream,
} from "./api/client.js";
import ChatPanel from "./components/ChatPanel.jsx";
import CreateSessionDialog from "./components/CreateSessionDialog.jsx";
import DeleteSessionDialog from "./components/DeleteSessionDialog.jsx";
import RightPanel from "./components/RightPanel.jsx";
import SessionSelect from "./components/SessionSelect.jsx";
import WelcomePage from "./components/WelcomePage.jsx";
import { syncCodeInMessages } from "./utils/syncCode.js";
import { getSessionIdFromUrl, setSessionIdInUrl } from "./utils/sessionUrl.js";
import { createTestEntry } from "./utils/testHistory.js";
import { resolveTestSnapshots } from "./utils/testChatContext.js";
import "./App.css";

function applySessionToState(session, setters) {
  setters.setMessages(session.messages ?? []);
  setters.setCode(session.code ?? "");
  setters.setInput(session.input_draft ?? "");
  setters.setTestFacts(session.test_facts ?? []);
  setters.setTestQueryTags(session.test_query ? [session.test_query] : []);
  setters.setTestHistory(session.test_history ?? []);
  setters.setActiveTab(session.active_tab === "test" ? "test" : "code");
  setters.setSessionId(session.id);
  setters.setSessionName(session.name ?? "");
  setters.setLogs([]);
  setters.setError(null);
  setters.setCodeSaveError(null);
}

function buildSessionPayload(state) {
  return {
    messages: state.messages,
    code: state.code,
    input_draft: state.input,
    test_facts: state.testFacts,
    test_query: state.testQueryTags[0] ?? "",
    test_history: state.testHistory,
    active_tab: state.activeTab,
  };
}

export default function App() {
  const [booting, setBooting] = useState(true);
  const [sessionId, setSessionId] = useState(null);
  const [sessionName, setSessionName] = useState("");
  const [sessions, setSessions] = useState([]);
  const [creatingSession, setCreatingSession] = useState(false);
  const [deletingSession, setDeletingSession] = useState(false);
  const [anthropicModel, setAnthropicModel] = useState("");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [code, setCode] = useState("");
  const [logs, setLogs] = useState([]);
  const [logActive, setLogActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState("code");
  const [running, setRunning] = useState(false);
  const [savingCode, setSavingCode] = useState(false);
  const [codeSaveError, setCodeSaveError] = useState(null);
  const [testFacts, setTestFacts] = useState([]);
  const [testQueryTags, setTestQueryTags] = useState([]);
  const [testHistory, setTestHistory] = useState([]);
  const [chatTestIds, setChatTestIds] = useState([]);

  const hydrated = useRef(false);
  const switching = useRef(false);
  const stateRef = useRef({});

  stateRef.current = {
    messages,
    code,
    input,
    testFacts,
    testQueryTags,
    testHistory,
    activeTab,
  };

  const refreshSessionList = useCallback(async () => {
    const list = await listSessions();
    setSessions(list);
    return list;
  }, []);

  const persistSession = useCallback(
    async (id) => {
      if (!id) return null;
      const saved = await updateSession(id, buildSessionPayload(stateRef.current));
      setSessionName(saved.name);
      await refreshSessionList();
      return saved;
    },
    [refreshSessionList],
  );

  const loadSession = useCallback(async (id) => {
    const session = await getSession(id);
    applySessionToState(session, {
      setMessages,
      setCode,
      setInput,
      setTestFacts,
      setTestQueryTags,
      setTestHistory,
      setActiveTab,
      setSessionId,
      setSessionName,
      setLogs,
      setError,
      setCodeSaveError,
    });
    return session;
  }, []);

  const clearWorkspace = useCallback(() => {
    setSessionId(null);
    setSessionName("");
    setMessages([]);
    setInput("");
    setCode("");
    setTestFacts([]);
    setTestQueryTags([]);
    setTestHistory([]);
    setChatTestIds([]);
    setActiveTab("code");
    setLogs([]);
    setCodeSaveError(null);
    setSessionIdInUrl(null);
  }, []);

  const handleAddTestToChat = useCallback((entryId) => {
    setChatTestIds((prev) => (prev.includes(entryId) ? prev : [...prev, entryId]));
  }, []);

  const handleRemoveChatTest = useCallback((entryId) => {
    setChatTestIds((prev) => prev.filter((id) => id !== entryId));
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const health = await checkHealth();
        if (!cancelled) {
          setAnthropicModel(health.anthropic_model ?? "");
        }

        await refreshSessionList();
        if (cancelled) return;

        const urlSessionId = getSessionIdFromUrl();
        if (urlSessionId) {
          try {
            await loadSession(urlSessionId);
            setSessionIdInUrl(urlSessionId);
          } catch {
            if (!cancelled) {
              setSessionIdInUrl(null);
              clearWorkspace();
              setError("Session not found. It may have been removed.");
            }
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message ?? "Failed to load sessions");
        }
      } finally {
        if (!cancelled) {
          hydrated.current = true;
          setBooting(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [refreshSessionList, loadSession, clearWorkspace]);

  useEffect(() => {
    const handlePopState = async () => {
      if (!hydrated.current || switching.current) return;

      const urlSessionId = getSessionIdFromUrl();
      if (urlSessionId === sessionId) return;

      switching.current = true;
      setError(null);

      try {
        if (sessionId) {
          await persistSession(sessionId);
        }

        if (!urlSessionId) {
          clearWorkspace();
          return;
        }

        await loadSession(urlSessionId);
      } catch (err) {
        setError(err.message ?? "Failed to open session");
        if (!getSessionIdFromUrl()) {
          clearWorkspace();
        }
      } finally {
        switching.current = false;
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [sessionId, loadSession, persistSession, clearWorkspace]);

  useEffect(() => {
    if (!hydrated.current || !sessionId || switching.current) return;

    const timer = setTimeout(() => {
      persistSession(sessionId).catch(() => {
        /* ignore autosave errors */
      });
    }, 600);

    return () => clearTimeout(timer);
  }, [
    messages,
    code,
    input,
    testFacts,
    testQueryTags,
    testHistory,
    activeTab,
    sessionId,
    persistSession,
  ]);

  const appendLog = useCallback((line) => {
    if (!line) return;
    setLogs((prev) => [...prev, line]);
  }, []);

  const appendSection = useCallback((title) => {
    setLogs((prev) => [...prev, "", `── ${title} ──`]);
  }, []);

  const pushTestResult = useCallback((entry) => {
    setTestHistory((prev) => [...prev, entry]);
  }, []);

  const handleOpenSession = async (nextId) => {
    if (!nextId || nextId === sessionId || loading || running || savingCode || creatingSession) {
      return;
    }

    switching.current = true;
    setError(null);
    try {
      if (sessionId) {
        await persistSession(sessionId);
      }
      await loadSession(nextId);
      setSessionIdInUrl(nextId);
    } catch (err) {
      setError(err.message ?? "Failed to open session");
    } finally {
      switching.current = false;
    }
  };

  const handleGoHome = useCallback(() => {
    if (loading || running || savingCode || creatingSession || deletingSession) return;
    clearWorkspace();
    setError(null);
  }, [clearWorkspace, loading, running, savingCode, creatingSession, deletingSession]);

  const handleConfirmDeleteSession = async () => {
    if (!sessionId || deletingSession) return;

    setDeletingSession(true);
    setError(null);
    switching.current = true;

    try {
      await deleteSession(sessionId);
      await refreshSessionList();
      setDeleteDialogOpen(false);
      clearWorkspace();
    } catch (err) {
      setError(err.message ?? "Failed to delete session");
    } finally {
      setDeletingSession(false);
      switching.current = false;
    }
  };

  const handleCreateSession = async (name) => {
    const trimmed = name.trim();
    if (!trimmed || creatingSession) return;

    setCreatingSession(true);
    setError(null);
    switching.current = true;

    try {
      if (sessionId) {
        await persistSession(sessionId);
      }
      const created = await createSession(trimmed);
      await refreshSessionList();
      applySessionToState(created, {
        setMessages,
        setCode,
        setInput,
        setTestFacts,
        setTestQueryTags,
        setTestHistory,
        setActiveTab,
        setSessionId,
        setSessionName,
        setLogs,
        setError,
        setCodeSaveError,
      });
      setCreateDialogOpen(false);
      setSessionIdInUrl(created.id);
    } catch (err) {
      setError(err.message ?? "Failed to create session");
    } finally {
      setCreatingSession(false);
      switching.current = false;
    }
  };

  const handleCodeSave = useCallback(
    async (newCode) => {
      setCodeSaveError(null);
      setSavingCode(true);
      setLogActive(true);
      setActiveTab("code");
      appendSection("user");

      try {
        const result = await validateSyntaxStream(newCode, {
          onLog: appendLog,
          onError: (message) => {
            appendLog(`Error: ${message}`);
            setCodeSaveError(message);
          },
        });

        if (!result) {
          const msg = "Syntax check did not complete.";
          appendLog(msg);
          setCodeSaveError(msg);
          return false;
        }

        if (result.ok) {
          appendLog("Code saved.");
          setCode(newCode);
          setMessages((prev) => syncCodeInMessages(prev, newCode));
          return true;
        }

        const msg =
          result.message ||
          "Syntax invalid. Fix the errors in the logs and try Save again.";
        appendLog(msg);
        setCodeSaveError(msg);
        return false;
      } catch (err) {
        const msg = err.message ?? "Syntax check failed";
        appendLog(`Error: ${msg}`);
        setCodeSaveError(msg);
        return false;
      } finally {
        setSavingCode(false);
        setLogActive(false);
      }
    },
    [appendLog, appendSection],
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    const text = input.trim();
    const testContext = resolveTestSnapshots(testHistory, chatTestIds);
    if ((!text && testContext.length === 0) || loading || !sessionId) return;

    const userMessage = {
      role: "user",
      content: text || "Please use the attached test result(s).",
      ...(testContext.length > 0 ? { test_context: testContext } : {}),
    };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setChatTestIds([]);
    setLoading(true);
    setLogActive(true);
    setError(null);
    appendSection("chat");

    try {
      await streamChat(nextMessages, code, {
        onLog: appendLog,
        onDone: (data) => {
          appendLog("Response ready.");
          const newCode = data.code ?? "";
          if (newCode.trim()) {
            setCode(newCode);
          } else if (!code.trim()) {
            setCode("");
          }
          const answerText = String(data.message ?? "").trim();
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content:
                data.assistant_content ??
                JSON.stringify({
                  message: answerText || "(No answer text returned.)",
                  code: data.code ?? "",
                }),
            },
          ]);
        },
        onError: (message) => {
          appendLog(`Error: ${message}`);
          setError(message);
        },
      });
    } catch (err) {
      const msg = err.message ?? "Something went wrong";
      appendLog(`Error: ${msg}`);
      setError(msg);
    } finally {
      setLoading(false);
      setLogActive(false);
    }
  };

  const handleRun = async () => {
    const query = testQueryTags[0]?.trim();
    if (!code.trim() || !query || running) return;
    setRunning(true);
    setError(null);

    try {
      const result = await runGorgiasQuery(code, query, testFacts);
      pushTestResult(
        createTestEntry("run", result, { query, facts: [...testFacts], code }),
      );
    } catch (err) {
      pushTestResult(
        createTestEntry("run", { ok: false, message: err.message }, {
          query,
          facts: [...testFacts],
          code,
        }),
      );
    } finally {
      setRunning(false);
    }
  };

  const busy =
    loading || running || savingCode || creatingSession || deletingSession || booting;
  const hasActiveSession = Boolean(sessionId);

  if (booting) {
    return (
      <div className="app app-booting">
        <p>Loading…</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <button
          type="button"
          className="app-title"
          onClick={handleGoHome}
          disabled={busy}
          title="Back to welcome"
        >
          Gorgias Chatbot
        </button>
        <div className="app-header-actions">
          {hasActiveSession && (
            <button
              type="button"
              className="btn-delete-session"
              onClick={() => setDeleteDialogOpen(true)}
              disabled={busy}
            >
              Delete session
            </button>
          )}
          <SessionSelect
            sessions={sessions}
            currentSessionId={sessionId}
            currentSessionName={sessionName}
            onSelect={handleOpenSession}
            onCreate={() => setCreateDialogOpen(true)}
            disabled={busy}
          />
        </div>
      </header>

      {error && !hasActiveSession && <p className="app-banner-error">{error}</p>}

      {hasActiveSession ? (
        <div className="app-layout">
          <ChatPanel
            messages={messages}
            input={input}
            onInputChange={setInput}
            onSubmit={handleSubmit}
            loading={loading}
            error={error}
            anthropicModel={anthropicModel}
            chatTestIds={chatTestIds}
            testHistory={testHistory}
            onRemoveChatTest={handleRemoveChatTest}
          />
          <RightPanel
            code={code}
            onCodeSave={handleCodeSave}
            onCodeEditStart={() => setCodeSaveError(null)}
            codeEditorDisabled={busy}
            codeSaveError={codeSaveError}
            savingCode={savingCode}
            logs={logs}
            logActive={logActive || loading || savingCode}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            onRun={handleRun}
            running={running}
            testHistory={testHistory}
            testFacts={testFacts}
            onTestFactsChange={setTestFacts}
            testQueryTags={testQueryTags}
            onTestQueryChange={setTestQueryTags}
            chatTestIds={chatTestIds}
            onAddTestToChat={handleAddTestToChat}
          />
        </div>
      ) : (
        <WelcomePage />
      )}

      <CreateSessionDialog
        open={createDialogOpen}
        onClose={() => !creatingSession && setCreateDialogOpen(false)}
        onCreate={handleCreateSession}
        creating={creatingSession}
      />

      <DeleteSessionDialog
        open={deleteDialogOpen}
        sessionName={sessionName}
        onClose={() => !deletingSession && setDeleteDialogOpen(false)}
        onConfirm={handleConfirmDeleteSession}
        deleting={deletingSession}
      />
    </div>
  );
}
