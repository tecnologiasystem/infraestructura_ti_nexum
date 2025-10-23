import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import CrearUsuario from '../pages/Administracion/Usuarios/Usuarios';
import Areas from '../pages/Administracion/Areas/Areas';
import Roles from '../pages/Administracion/Roles/Roles';
import Campanas from '../pages/Administracion/Campanas/Campanas';
import PrediccionIA from '../pages/IA/PrediccionIA/PrediccionIA';
import SMS from '../pages/Notificaciones/SMS/SMS';
import Administracion from '../pages/Administracion/Administracion';
import InteligenciaArtificial from '../pages/IA/InteligenciaArtificial';
import Notificaciones from '../pages/Notificaciones/Notificaciones';
import Planeacion from '../pages/Planeacion/Planeacion';
import FocoTrabajable from '../pages/Planeacion/Focos/FocoTrabajable/FocoTrabajable';
import FocoResultado from '../pages/Planeacion/Focos/FocoResultado/FocoResultado';
import Chat from '../pages/Chat/Chat';
import ImpulsoProcesal from '../pages/Juridica/pages/ImpulsoProcesalPage';
import Gail from '../pages/Planeacion/Focos/Gail/Busquedas';
import EmailMasivo from '../pages/Correos/ImpulsoEmail';
import RpaVigilancia from '../pages/Automatizaciones/rpaVigilancia';
import RpaSuperNotariado from '../pages/Automatizaciones/rpaSuperNotariado';
import RpaRunt from '../pages/Automatizaciones/rpaRunt';
import TableroControl from '../pages/Administracion/TableroControl';
import CampanasGail from '../pages/Planeacion/Focos/Gail/CampanasGail';
import ResumenCampana from '../pages/Planeacion/Focos/Gail/ResumenCampanas';
import RpaRues from '../pages/Automatizaciones/rpaRues';
import ConversorExcel from '../pages/Conversor/conversorExcel';
import ImportarLlamadas from '../pages/Integracion/IntegracionLlamadas';
import RpaFamiSanar from '../pages/Automatizaciones/rpaFamiSanar';
import TableroEmbudo from '../pages/Tableros/TableroEmbudo';
import ProjectManager from '../pages/ProjectManager/ProjectManager';
import RpaSimit  from '../pages/Automatizaciones/rpaSimit';
import RpaNuevaEps from '../pages/Automatizaciones/rpaNuevaEps';
import TableroControlRPA from '../pages/Tableros/ControlRpa';
import RpaWhatsApp from '../pages/Automatizaciones/rpaWhatsApp';
import RpaCamaraComercio from '../pages/Automatizaciones/rpaCamaraComercio';
import RpaJuridico from '../pages/Automatizaciones/rpaJuridico';
import RpaTyba from '../pages/Automatizaciones/rpaTyba';
import RpaVigencia from '../pages/Automatizaciones/rpaVigencia';
import RpaMensajesWhatsApp from '../pages/Automatizaciones/rpaMensajesWhatsApp';
import MensajesWhatsapp from '../pages/WhatsApp/mensajesWhatsApp';
import AcuerdoPago from '../pages/AcuerdosPago/AcuerdoPago';
import DocumentPersonalizer from '../pages/Correos/DocumentPersonalizer';
import ReportesWhatsApp from '../pages/WhatsApp/reportesWhatsapp';
import EmailReporte from '../pages/Correos/EmailReporte';

const RutaProtegida = ({ children, ruta }) => {
  const permisos = JSON.parse(localStorage.getItem("permisos") || "[]");
  const tienePermiso = permisos.some(p => p.ruta === ruta && p.permisoVer);
  return tienePermiso ? children : <Navigate to="/home" />;
};

const AppRouter = () => {
  return (
    <Routes>
      <Route path="/home" element={<HomePage />} />
      
      <Route path="/EmailMasivo" element={<EmailMasivo />} /> 

      <Route path="/acuerdoPago" element={<AcuerdoPago />} />

      <Route path="/email-reporte" element={<EmailReporte />} />

      <Route path="/documentos" element={<DocumentPersonalizer />} />
            <Route path="/reportesWhatsapp" element={<ReportesWhatsApp />} />
      
      <Route path="/conversor" element={
        <RutaProtegida ruta="/conversor">
          <ConversorExcel />
        </RutaProtegida>
      } />

      <Route path="/chat" element={<Chat />} />
      <Route path="/tableroControl" element={
        <RutaProtegida ruta="/tableroControl">
          <TableroControl />
        </RutaProtegida>
      } />

      <Route path="/administracion/administracionGrafica" element={
        <RutaProtegida ruta="/administracion/administracionGrafica">
          <Administracion />
        </RutaProtegida>
      } />
      <Route path="/administracion/usuarios" element={
        <RutaProtegida ruta="/administracion/usuarios">
          <CrearUsuario />
        </RutaProtegida>
      } />
      <Route path="/administracion/areas" element={
        <RutaProtegida ruta="/administracion/areas">
          <Areas />
        </RutaProtegida>
      } />
      <Route path="/administracion/roles" element={
        <RutaProtegida ruta="/administracion/roles">
          <Roles />
        </RutaProtegida>
      } />
      <Route path="/administracion/campanas" element={
        <RutaProtegida ruta="/administracion/campanas">
          <Campanas />
        </RutaProtegida>
      } />

      <Route path="/ia" element={
        <RutaProtegida ruta="/ia">
          <InteligenciaArtificial />
        </RutaProtegida>
      } />
      <Route path="/ia/prediccion" element={
        <RutaProtegida ruta="/ia/prediccion">
          <PrediccionIA />
        </RutaProtegida>
      } />

      <Route path="/notificaciones" element={
        <RutaProtegida ruta="/notificaciones">
          <Notificaciones />
        </RutaProtegida>
      } />
      <Route path="/notificaciones/SMS" element={
        <RutaProtegida ruta="/notificaciones/SMS">
          <SMS />
        </RutaProtegida>
      } />

      <Route path="/planeacion" element={
        <RutaProtegida ruta="/planeacion">
          <Planeacion />
        </RutaProtegida>
      } />
      <Route path="/planeacion/focosTrabajable" element={
        <RutaProtegida ruta="/planeacion/focosTrabajable">
          <FocoTrabajable />
        </RutaProtegida>
      } />
      <Route path="/planeacion/focosResultado" element={
        <RutaProtegida ruta="/planeacion/focosResultado">
          <FocoResultado />
        </RutaProtegida>
      } />
      <Route path="/gail/busquedas" element={
        <RutaProtegida ruta="/gail/busquedas">
          <Gail />
        </RutaProtegida>

      } />
      <Route path="/gail/campañas" element={
        <RutaProtegida ruta="/gail/campañas">
          <CampanasGail />
        </RutaProtegida>
      } />
      <Route path='/gail/resumen' element={
        <ResumenCampana />
      } />
      <Route path="/juridica/impulsoProcesal" element={
        <RutaProtegida ruta="/juridica/impulsoProcesal">
          <ImpulsoProcesal />
        </RutaProtegida>
      } />
      
      <Route path="/juridica/rpaVigilancia" element={
        <RutaProtegida ruta="/juridica/rpaVigilancia">
          <RpaVigilancia />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaSuperNotariado" element={
        <RutaProtegida ruta="/juridica/rpaSuperNotariado">
          <RpaSuperNotariado />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaRunt" element={
        <RutaProtegida ruta="/juridica/rpaRunt">
          <RpaRunt />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaRues" element={
        <RutaProtegida ruta="/juridica/rpaRues">
          <RpaRues />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaSimit" element={
        <RutaProtegida ruta="/juridica/rpaSimit">
          <RpaSimit />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaCamaraComercio" element={
        <RutaProtegida ruta="/juridica/rpaCamaraComercio">
          <RpaCamaraComercio />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaJuridico" element={
        <RutaProtegida ruta="/juridica/rpaJuridico">
          <RpaJuridico />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaTyba" element={
        <RutaProtegida ruta="/juridica/rpaTyba">
          <RpaTyba />
        </RutaProtegida>
      } />
      <Route path="/juridica/rpaVigencia" element={
        <RutaProtegida ruta="/juridica/rpaVigencia">
          <RpaVigencia />
        </RutaProtegida>
      } />
      <Route path="/salud/rpaFamisanar" element={
        <RutaProtegida ruta="/salud/rpaFamisanar">
          <RpaFamiSanar />
        </RutaProtegida>
      } />
      <Route path="/salud/rpaNuevaEps" element={
        <RutaProtegida ruta="/salud/rpaNuevaEps">
          <RpaNuevaEps />
        </RutaProtegida>
      } />
      <Route path="/importarLlamadas" element={
        <RutaProtegida ruta="/importarLlamadas">
          <ImportarLlamadas />
        </RutaProtegida>
      } />
      <Route path="/tableroEmbudo" element={
        <RutaProtegida ruta="/tableroEmbudo">
          <TableroEmbudo />
        </RutaProtegida>
      } />
      <Route path="/projectManager" element={
        <RutaProtegida ruta="/projectManager">
          <ProjectManager />
        </RutaProtegida>
      } />
      <Route path="/controlRpa" element={
        <RutaProtegida ruta="/controlRpa">
          <TableroControlRPA />
        </RutaProtegida>
      } />
      <Route path="/rpaWhatsApp" element={
        <RutaProtegida ruta="/rpaWhatsApp">
          <RpaWhatsApp />
        </RutaProtegida>
      } />
      <Route path="/rpaMensajesWhatsApp" element={
        <RutaProtegida ruta="/rpaMensajesWhatsApp">
          <RpaMensajesWhatsApp />
        </RutaProtegida>
      } />

       <Route path="/mensajesWhatsApp" element={
        <RutaProtegida ruta="/mensajesWhatsApp">
          <MensajesWhatsapp />
        </RutaProtegida>
      } />
    </Routes>
  );
};

export default AppRouter;
