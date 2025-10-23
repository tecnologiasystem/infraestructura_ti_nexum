import React from "react";
import "./infoPopup.css";

const InfoPopup = ({ title, message, onClose }) => {
  return (
    <div className="popup-overlay">
      <div className="popup-content">
        <h3>{title}</h3>
        <p>{message}</p>
        <button className="popup-btn" onClick={onClose}>Entendido</button>
      </div>
    </div>
  );
};

export default InfoPopup;
