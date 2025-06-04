import React, { useState, useEffect } from "react";
import { FaThumbsUp, FaThumbsDown } from "react-icons/fa";
import { IoMdClose } from "react-icons/io";
import axios from "axios";
import {
  FeedbackContainer,
  FeedbackButton,
  SuggestionInput,
  SuggestionContainer,
  FeedbackMessage,
  DeleteButton,
} from "./Feedback.styles";

const Feedback = ({ answerId }) => {
  const [feedback, setFeedback] = useState(null);
  const [suggestion, setSuggestion] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchFeedback();
  }, [answerId]);

  const fetchFeedback = async () => {
    try {
      const response = await axios.get(`/api/feedback?answer_id=${answerId}`);
      if (response.data) {
        setFeedback(response.data);
        setSuggestion(response.data.suggestion || "");
      } else {
        setFeedback(null);
        setSuggestion("");
      }
    } catch (error) {
      console.error("Error fetching feedback:", error);
    }
  };

  const handleThumbsUp = async () => {
    setIsSubmitting(true);
    setMessage("");
    try {
      if (feedback?.like === true) {
        // Clicking again deletes feedback
        const response = await axios.delete(
          `/api/feedback?answer_id=${answerId}`
        );
        if (response.data.success) {
          setFeedback(null);
          setSuggestion("");
          setMessage("Feedback deleted");
        }
      } else {
        const response = await axios.post("/api/feedback", {
          answer_id: answerId,
          like: true,
          suggestion: null,
        });
        if (response.data.feedback_id) {
          setFeedback({ like: true, suggestion: null });
          setMessage("Feedback saved successfully");
        }
      }
    } catch (error) {
      console.error("Error saving/deleting feedback:", error);
      setMessage("Failed to save/delete feedback");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleThumbsDown = async () => {
    setIsSubmitting(true);
    setMessage("");
    try {
      if (feedback?.like === false) {
        // Clicking again deletes feedback
        const response = await axios.delete(
          `/api/feedback?answer_id=${answerId}`
        );
        if (response.data.success) {
          setFeedback(null);
          setSuggestion("");
          setMessage("Feedback deleted");
        }
      } else {
        const response = await axios.post("/api/feedback", {
          answer_id: answerId,
          like: false,
          suggestion: null,
        });
        if (response.data.feedback_id) {
          setFeedback({ like: false, suggestion: null });
          setMessage("Feedback saved successfully");
        }
      }
    } catch (error) {
      console.error("Error saving/deleting feedback:", error);
      setMessage("Failed to save/delete feedback");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitSuggestion = async () => {
    setIsSubmitting(true);
    setMessage("");
    try {
      const response = await axios.post("/api/feedback", {
        answer_id: answerId,
        like: false,
        suggestion,
      });
      if (response.data.feedback_id) {
        setFeedback({ like: false, suggestion });
        setMessage("Feedback updated with suggestion");
      }
    } catch (error) {
      console.error("Error saving suggestion:", error);
      setMessage("Failed to update feedback");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show submit button only if thumbs down is selected and suggestion is different from last saved
  const showSubmit =
    feedback?.like === false &&
    suggestion.trim() !== (feedback.suggestion || "");

  return (
    <div>
      <FeedbackContainer>
        <FeedbackButton
          onClick={handleThumbsUp}
          disabled={isSubmitting}
          active={feedback?.like === true}
          title="Thumbs up"
        >
          <FaThumbsUp size={20} />
        </FeedbackButton>
        <FeedbackButton
          onClick={handleThumbsDown}
          disabled={isSubmitting}
          active={feedback?.like === false}
          title="Thumbs down"
        >
          <FaThumbsDown size={20} />
        </FeedbackButton>
      </FeedbackContainer>

      {feedback?.like === false && (
        <SuggestionContainer>
          <SuggestionInput
            value={suggestion}
            onChange={(e) => setSuggestion(e.target.value)}
            placeholder="What would be a better answer? (optional)"
            disabled={isSubmitting}
          />
          {showSubmit && (
            <button
              onClick={handleSubmitSuggestion}
              disabled={isSubmitting || suggestion.trim() === ""}
              style={{
                marginTop: 8,
                padding: "6px 16px",
                borderRadius: 4,
                background: "#2563eb",
                color: "white",
                border: "none",
                fontWeight: "bold",
                cursor:
                  isSubmitting || suggestion.trim() === ""
                    ? "not-allowed"
                    : "pointer",
              }}
            >
              Submit
            </button>
          )}
        </SuggestionContainer>
      )}

      {message && <FeedbackMessage>{message}</FeedbackMessage>}
    </div>
  );
};

export default Feedback;
