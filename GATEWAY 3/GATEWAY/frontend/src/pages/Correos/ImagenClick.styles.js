import styled, { createGlobalStyle, keyframes } from "styled-components";

// Animaciones
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
`;

const pulse = keyframes`
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
`;

// Estilos Globales
export const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body { 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #ffffffff 0%, #1d3eacff 100%);
    color: #1a1a2e;
    min-height: 100vh;
    padding: 2rem 1rem;
  }
`;

export const Container = styled.div`
  max-width: 1600px;
  margin: 0 auto;
  animation: ${fadeIn} 0.6s ease;
`;

export const Header = styled.div`
  text-align: center;
  margin-top: 3rem;
  
  h1 {
    font-size: 2rem;
    font-weight: 800;
    color: #1d3eacff;
    text-shadow: 0 2px 10px hsla(0, 0%, 0%, 0.20);
    margin-bottom: 0.5rem;
  }
  
  p {
    color: #1d3eacff;
    font-size: 1.1rem;
  }
`;

export const Select = styled.select`
  padding: 8px;
  border-radius: 6px;
`;

export const MainGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

export const LeftColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

export const RightColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

export const Card = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
  }
`;

export const CardTitle = styled.h2`
  font-size: 1.3rem;
  font-weight: 700;
  color: #2d3748;
  margin-top: 1rem;
  margin-bottom: 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  svg {
    color: #1d3eacff;
  }
`;

export const FileUploadArea = styled.div`
  border: 2px dashed ${props => props.hasFile ? '#48bb78' : '#cbd5e0'};
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  background: ${props => props.hasFile ? '#f0fff4' : '#f7fafc'};
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #667eea;
    background: #edf2f7;
  }
  
  svg {
    font-size: 2.5rem;
    color: ${props => props.hasFile ? '#48bb78' : '#a0aec0'};
    margin-bottom: 0.75rem;
  }
  
  p {
    color: #4a5568;
    font-weight: 500;
    margin-bottom: 0.25rem;
  }
  
  span {
    color: #718096;
    font-size: 0.875rem;
  }
`;

export const Input = styled.input`
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

export const TextArea = styled.textarea`
  width: 100%;
  min-height: 120px;
  padding: 0.875rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  transition: all 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

export const FormGroup = styled.div`
  margin-bottom: 1.25rem;
  
  label {
    display: block;
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
  }
  
  small {
    display: block;
    color: #718096;
    font-size: 0.85rem;
    margin-top: 0.35rem;
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 0.875rem 1.5rem;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

export const PrimaryButton = styled(Button)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
  }
`;

export const SecondaryButton = styled(Button)`
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(245, 87, 108, 0.5);
  }
`;

export const TertiaryButton = styled(Button)`
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79, 172, 254, 0.5);
  }
`;

export const UrlList = styled.div`
  background: #f7fafc;
  border-radius: 10px;
  padding: 1rem;
  margin-top: 1rem;
  max-height: 250px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #e2e8f0;
    border-radius: 10px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #cbd5e0;
    border-radius: 10px;
  }
`;

export const UrlItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  
  &:last-child {
    margin-bottom: 0;
  }
`;

export const UrlDot = styled.span`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #48bb78;
  flex-shrink: 0;
`;

export const UrlLink = styled.a`
  flex: 1;
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  
  &:hover {
    text-decoration: underline;
  }
`;

export const DeleteButton = styled.button`
  background: none;
  border: none;
  color: #e53e3e;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.3s ease;
  
  &:hover {
    background: #fff5f5;
    transform: scale(1.1);
  }
`;

export const ImageSection = styled.div`
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
`;

export const ImageContainer = styled.div`
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #f7fafc;
  border: 2px solid #e2e8f0;
`;

export const Image = styled.img`
  width: 100%;
  display: block;
  cursor: crosshair;
  user-select: none;
`;

export const RemoveImageButton = styled.button`
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10;
  background: rgba(229, 62, 62, 0.95);
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  
  &:hover {
    background: #c53030;
    transform: scale(1.05);
  }
`;

export const ClickableArea = styled.div`
  position: absolute;
  left: ${p => p.x}px;
  top: ${p => p.y}px;
  width: ${p => p.width}px;
  height: ${p => p.height}px;
  border: 2px dashed #48bb78;
  background: rgba(72, 187, 120, 0.15);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(72, 187, 120, 0.25);
    border-color: #38a169;
  }
`;

export const SelectedArea = styled.div`
  position: absolute;
  border: 2px solid #667eea;
  background: rgba(102, 126, 234, 0.2);
  pointer-events: none;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.4);
`;

export const UrlInputRow = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
  animation: ${fadeIn} 0.3s ease;
`;

export const UrlInput = styled(Input)`
  flex: 1;
`;

export const SaveUrlButton = styled.button`
  padding: 0.875rem 1.5rem;
  background: #48bb78;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &:hover {
    background: #38a169;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
  }
`;