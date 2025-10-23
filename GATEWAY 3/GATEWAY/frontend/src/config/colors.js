const allowedColors = [
    '#36A2DA', // Azul claro
    '#EE8D00', // Naranja
    '#90BC1F', // Verde
    '#662480', // Morado
  ];
  
  // Degradados corregidos con 70% color fuerte y 30% más claro
  const gradients = {
    '#36A2DA': 'linear-gradient(135deg, #36A2DA 0%, #36A2DA 70%, #A7D5F4 100%)',
    '#EE8D00': 'linear-gradient(135deg, #EE8D00 0%, #EE8D00 70%, #FFB84D 100%)',
    '#90BC1F': 'linear-gradient(135deg, #90BC1F 0%, #90BC1F 70%, #D4E897 100%)',
    '#662480': 'linear-gradient(135deg, #662480 0%, #662480 70%, #B98DD1 100%)',
  };
  
  const getGradient = (color) => {
    return gradients[color] || 'linear-gradient(135deg, #eeeeee 0%, #ffffff 100%)';
  };
  
  const isColorDark = (hexColor) => {
    // Remover el # si lo tiene
    const color = hexColor.replace('#', '');
    const r = parseInt(color.substr(0, 2), 16);
    const g = parseInt(color.substr(2, 2), 16);
    const b = parseInt(color.substr(4, 2), 16);
    // Formula estándar para calcular luminancia
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness < 128; // Si es menor a 128 se considera oscuro
  };
  
  export { allowedColors, gradients, getGradient, isColorDark };
  