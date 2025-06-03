import styled from "styled-components";

export const FeedbackContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
`;

export const FeedbackButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
  color: ${(props) => (props.active ? "#1a73e8" : "#666")};

  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }

  &:active {
    background-color: rgba(0, 0, 0, 0.1);
  }
`;

export const SuggestionInput = styled.textarea`
  width: 100%;
  min-height: 60px;
  padding: 8px;
  margin-top: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;

  &:focus {
    outline: none;
    border-color: #1a73e8;
  }
`;

export const SuggestionContainer = styled.div`
  margin-top: 8px;
  width: 100%;
`;

export const FeedbackMessage = styled.div`
  font-size: 12px;
  color: #666;
  margin-top: 4px;
`;

export const DeleteButton = styled.button`
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 12px;
  padding: 4px;
  margin-left: 8px;

  &:hover {
    color: #d32f2f;
  }
`;
