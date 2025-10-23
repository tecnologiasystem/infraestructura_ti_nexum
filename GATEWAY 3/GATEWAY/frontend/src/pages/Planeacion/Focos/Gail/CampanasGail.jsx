import React, { useState, useEffect } from "react";
import {
  Table,
  Button,
  Space,
  Input,
  Modal,
  Tooltip,
  Select,
  notification,
  Form,
  InputNumber,
  Row,
  Col,
  Tag,
  Spin,
  Descriptions,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  SearchOutlined,
  MinusCircleOutlined,
  EyeOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
} from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../../../config";
import "./CampanasGail.css";
import {
  LULA_API_KEY_DOMINICANA,
  LULA_API_KEY_SYSTEMGROUPCOBRO,
  LULA_API_KEY_SYSTEMGROUP,
  LULA_API_KEY_DISLICORES,
  LULA_API_KEY_OPERACION_PERU,
} from "../../../../config";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
} from "chart.js";
import { Pie } from "react-chartjs-2";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { TimePicker } from "antd";
import moment from "moment-timezone";
import { Upload } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import { Dropdown, Menu } from "antd";
import { PlayCircleOutlined, PauseCircleOutlined } from "@ant-design/icons";

ChartJS.register(ArcElement, ChartTooltip, Legend);

moment.tz.setDefault("America/Bogota");

const formatCurrency = (value) => {
  if (
    typeof value === "number" ||
    (typeof value === "string" && !isNaN(Number(value)) && value.trim() !== "")
  ) {
    const num = Number(value);
    if (isNaN(num)) return value;
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  }
  return value;
};

const defaultAdditionalDataFields = [
  { key: "Banco", value: "" },
  { key: "Cedula", value: "" },
  { key: "Capital", value: "" },
  { key: "Oferta 1", value: "" },
  { key: "Oferta 2", value: "" },
  { key: "Oferta 3", value: "" },
  { key: "Producto", value: "" },
  { key: "Intereses", value: "" },
  { key: "Saldo total", value: "" },
  { key: "Ultimos digitos", value: "" },
  { key: "Genero", value: "" },
  { key: "Ciudad", value: "" },
  { key: "Pago Flexible", value: "" },
  { key: "Hasta 3 cuotas", value: "" },
  { key: "Hasta 6 cuotas", value: "" },
  { key: "Hasta 12 cuotas", value: "" },
  { key: "Inbound", value: "" },
  { key: "Tipo Acuerdo", value: "" },
  { key: "Valor de pago ", value: "" },
  { key: "Fecha de pago ", value: "" },
];

const CampanasGail = () => {
  const [selectedOutcomeFilter, setSelectedOutcomeFilter] = useState(null);
  const [data, setData] = useState([]);
  const [newDescripcion, setNewDescripcion] = useState("");
  const [sequences, setSequences] = useState([]);
  const [filteredSequences, setFilteredSequences] = useState([]);
  const [searchSequence, setSearchSequence] = useState("");
  const [contactLists, setContactLists] = useState([]);
  const [filteredContactLists, setFilteredContactLists] = useState([]);
  const [searchContactList, setSearchContactList] = useState("");
  const [redialingRules, setRedialingRules] = useState([]);
  const [filteredRedialingRules, setFilteredRedialingRules] = useState([]);
  const [searchRedialingRule, setSearchRedialingRule] = useState("");
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedSequence, setSelectedSequence] = useState(null);
  const [selectedContactList, setSelectedContactList] = useState(null);
  const [selectedRedialingRule, setSelectedRedialingRule] = useState(null);
  const [selectedCampaignName, setSelectedCampaignName] = useState("");
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);
  const [searchText, setSearchText] = useState("");
  const [lulaCreateModalVisible, setLulaCreateModalVisible] = useState(false);
  const [sequencesManageModalVisible, setSequencesManageModalVisible] =
    useState(false);
  const [editSequenceModalVisible, setEditSequenceModalVisible] =
    useState(false);
  const [editingSequence, setEditingSequence] = useState(null);
  const [contactListsManageModalVisible, setContactListsManageModalVisible] =
    useState(false);
  const [contactsInListModalVisible, setContactsInListModalVisible] =
    useState(false);
  const [currentContactListId, setCurrentContactListId] = useState(null);
  const [contactsInList, setContactsInList] = useState([]);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [additionalDataModalVisible, setAdditionalDataModalVisible] =
    useState(false);
  const [currentAdditionalData, setCurrentAdditionalData] = useState({});
  const [createContactListModalVisible, setCreateContactListModalVisible] =
    useState(false);
  const [newContactListName, setNewContactListName] = useState("");
  const [newContactListDescription, setNewContactListDescription] =
    useState("");
  const [addContactModalVisible, setAddContactModalVisible] = useState(false);
  const [
    selectedContactListForAddingContact,
    setSelectedContactListForAddingContact,
  ] = useState(null);
  const [addContactForm] = Form.useForm();
  const [
    redialingRulesManageModalVisible,
    setRedialingRulesManageModalVisible,
  ] = useState(false);
  const [redialingRuleDetailModalVisible, setRedialingRuleDetailModalVisible] =
    useState(false);
  const [currentRedialingRuleDetails, setCurrentRedialingRuleDetails] =
    useState(null);
  const [loadingRedialingRuleDetails, setLoadingRedialingRuleDetails] =
    useState(false);
  const [touchpointsModalVisible, setTouchpointsModalVisible] = useState(false);
  const [campaignTouchpoints, setCampaignTouchpoints] = useState([]);
  const [touchpointsLoading, setTouchpointsLoading] = useState(false);
  const [currentCampaignForTouchpoints, setCurrentCampaignForTouchpoints] =
    useState(null);
  const [searchTextGlobal, setSearchTextGlobal] = useState("");
  const [searchedColumn, setSearchedColumn] = useState("");
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [availableContactLists, setAvailableContactLists] = useState([]);
  const [availableSequences, setAvailableSequences] = useState([]);
  const [availableRules, setAvailableRules] = useState([]);
  const [selectedOrigenFilter, setSelectedOrigenFilter] = useState("todos");
  const [modoCreacionLibre, setModoCreacionLibre] = useState(false);
  const timezones = moment.tz.names();
  const [scriptOptions, setScriptOptions] = useState([]);
  const [selectedScriptId, setSelectedScriptId] = useState(null);
  const [loadingScripts, setLoadingScripts] = useState(false);
  const [createSequenceModalVisible, setCreateSequenceModalVisible] =
    useState(false);
  const [dataCampanas, setDataCampanas] = useState([]);
  const [opcionesSecuencia, setOpcionesSecuencia] = useState([]);
  const [opcionesListaContactos, setOpcionesListaContactos] = useState([]);
  const [opcionesRemarcado, setOpcionesRemarcado] = useState([]);
  const [modalCountry, setModalCountry] = useState(null);
  const [modalApiKey, setModalApiKey] = useState(null);
  const [availableContactListsModal, setAvailableContactListsModal] = useState(
    []
  );
  const [availableSequencesModal, setAvailableSequencesModal] = useState([]);
  const [availableRulesModal, setAvailableRulesModal] = useState([]);
  const [bulkContacts, setBulkContacts] = useState([]);
  const [creatingCampaign, setCreatingCampaign] = useState(false);
  const [loadingExcel, setLoadingExcel] = useState(false);
  const [form] = Form.useForm();
  const API_KEYS_BY_COUNTRY = {
    Dominicana: LULA_API_KEY_DOMINICANA,
    "SystemGroup Cobro": LULA_API_KEY_SYSTEMGROUPCOBRO,
    SystemGroup: LULA_API_KEY_SYSTEMGROUP,
    Dislicores: LULA_API_KEY_DISLICORES,
    "Operacion Peru": LULA_API_KEY_OPERACION_PERU,
  };

  const [paisSeleccionado, setPaisSeleccionado] = useState("Dominicana");
  const [apiKeyActiva, setApiKeyActiva] = useState(
    API_KEYS_BY_COUNTRY["Dominicana"]
  );

  const getApiKeyForCountry = (pais) => API_KEYS_BY_COUNTRY[pais] ?? null;

  useEffect(() => {
    fetchCampanas();
    setAvailableContactLists([]);
    setAvailableSequences([]);
    setAvailableRules([]);
  }, []);

  useEffect(() => {
    if (!apiKeyActiva) return;

    fetchScripts(apiKeyActiva);
    fetchSequences();
    fetchContactLists();
    fetchRedialingRules();
  }, [apiKeyActiva]);

  useEffect(() => {
    if (modalApiKey) {
      fetchScripts(modalApiKey);
    }
  }, [modalApiKey]);

  useEffect(() => {
    const cargarCampanas = async () => {
      try {
        const res = await fetch("https://api.lula.com/v1/campaigns", {
          headers: {
            "X-API-Key": apiKeyActiva,
            accept: "application/json",
          },
        });
        const data = await res.json();
        setDataCampanas(data);
      } catch (err) {
        console.error("Error al cargar campañas", err);
      }
    };

    if (apiKeyActiva) cargarCampanas();
  }, [apiKeyActiva]);

  useEffect(() => {
    if (!modalCountry || !modalApiKey) return;

    const fetchModalData = async () => {
      try {
        console.log(
          "Cargando datos del modal para país:",
          modalCountry,
          "con API Key:",
          modalApiKey
        );

        // Cargar listas de contacto
        const listsResponse = await fetch(
          "https://api.lula.com/v1/contact_lists?status=active",
          {
            headers: {
              accept: "text/plain",
              "X-API-Key": modalApiKey,
            },
          }
        );
        const lists = listsResponse.ok ? await listsResponse.json() : [];

        // Cargar secuencias
        const seqsResponse = await fetch(
          "https://api.lula.com/v1/sequences?status=active",
          {
            headers: {
              accept: "text/plain",
              "X-API-Key": modalApiKey,
            },
          }
        );
        const seqs = seqsResponse.ok ? await seqsResponse.json() : [];

        // Cargar reglas de remarcado
        const rulesResponse = await fetch(
          "https://api.lula.com/v1/redialing_rules",
          {
            headers: {
              accept: "application/json",
              "X-API-Key": modalApiKey,
            },
          }
        );
        const rules = rulesResponse.ok ? await rulesResponse.json() : [];

        console.log("Reglas cargadas para el modal:", rules);

        setAvailableContactLists(lists);
        setAvailableSequences(seqs);
        setAvailableRules(rules);
        setAvailableSequencesModal(seqs);
        setAvailableContactListsModal(lists);
        setAvailableRulesModal(rules);
      } catch (error) {
        console.error("Error al cargar datos de modal", error);
        notification.error({
          message: "Error al cargar recursos",
          description: error.message,
        });
      }
    };

    fetchModalData();
  }, [modalCountry, modalApiKey]);

  useEffect(() => {
    if (!selectedCountry) return;

    const fetchData = async () => {
      const [lists, seqs, rules] = await Promise.all([
        fetch(
          `${API_URL_GATEWAY}/gateway/campanas/contact_lists/${selectedCountry}`
        ).then((r) => r.json()),
        fetch(
          `${API_URL_GATEWAY}/gateway/campanas/secuencias/${selectedCountry}`
        ).then((r) => r.json()),
        fetch(
          `${API_URL_GATEWAY}/gateway/campanas/reglas/${selectedCountry}`
        ).then((r) => r.json()),
      ]);
      setAvailableContactLists(lists);
      setAvailableSequences(seqs);
      setAvailableRules(rules);
    };

    fetchData();
  }, [selectedCountry]);

  const startGailCampaign = async (record) => {
    const apiKey = getApiKeyForCountry(record.pais);
    if (!apiKey) {
      return notification.error({
        message: "API‑Key no encontrada para el país.",
      });
    }

    const accion = "start";

    try {
      const res = await fetch(
        `https://api.lula.com/v1/campaigns/${record.idCampana}/${accion}`,
        {
          method: "POST",
          headers: {
            "X-API-Key": apiKey,
            accept: "application/json",
          },
        }
      );

      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        console.error("❌ Lula responde 4xx/5xx:", body);
        throw new Error(body.message || `HTTP ${res.status}`);
      }

      notification.success({
        message:
          accion === "resume"
            ? "Campaña reanudada en Gail"
            : "Campaña iniciada en Gail",
      });
      fetchCampanas();
    } catch (err) {
      notification.error({
        message: "Error al iniciar campaña",
        description: err.message,
      });
    }
  };

  const stopGailCampaign = async (record) => {
    const apiKey = getApiKeyForCountry(record.pais);
    if (!apiKey)
      return notification.error({
        message: "API‑Key no encontrada para el país.",
      });

    try {
      const res = await fetch(
        `https://api.lula.com/v1/campaigns/${record.idCampana}/stop`,
        {
          method: "POST",
          headers: { "X-API-Key": apiKey, accept: "text/plain" },
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      notification.success({ message: "Campaña detenida en Gail" });
      fetchCampanas();
    } catch (err) {
      notification.error({
        message: "Error al detener campaña",
        description: err.message,
      });
    }
  };

  const fetchContactLists = async () => {
    try {
      const activeResponse = await fetch(
        "https://api.lula.com/v1/contact_lists?status=active",
        {
          headers: {
            accept: "text/plain",
            "X-API-Key": apiKeyActiva,
          },
        }
      );
      if (!activeResponse.ok)
        throw new Error(
          `Error ${activeResponse.status} al obtener listas de contacto activas`
        );
      const activeContactLists = await activeResponse.json();

      const archivedResponse = await fetch(
        "https://api.lula.com/v1/contact_lists?status=archived",
        {
          headers: {
            accept: "text/plain",
            "X-API-Key": apiKeyActiva,
          },
        }
      );
      if (!archivedResponse.ok)
        throw new Error(
          `Error ${archivedResponse.status} al obtener listas de contacto archivadas`
        );
      const archivedContactLists = await archivedResponse.json();

      const uniqueById = new Map();
      [...activeContactLists, ...archivedContactLists].forEach((list) => {
        uniqueById.set(list.id, list);
      });

      const allContactLists = Array.from(uniqueById.values());

      setContactLists(allContactLists);
      setFilteredContactLists(allContactLists);
    } catch (error) {
      console.error("Error al obtener listas de contacto:", error);
      notification.error({
        message: `Error al obtener listas de contacto: ${error.message}`,
      });
    }
  };

  const fetchScripts = async (apiKey) => {
    setLoadingScripts(true);
    try {
      const response = await fetch(
        "https://api.lula.com/v1/scripts?direction=outbound&status=active",
        {
          headers: {
            "X-API-Key": apiKey,
            Accept: "application/json",
          },
        }
      );

      const data = await response.json();
      setScriptOptions(
        data.map((script) => ({ label: script.name, value: script.id }))
      );
    } catch (error) {
      console.error("Error al obtener scripts:", error);
      notification.error({ message: "No se pudieron cargar los scripts" });
    } finally {
      setLoadingScripts(false);
    }
  };

  const fetchContactsInList = async (listId) => {
    setLoadingContacts(true);
    try {
      const key = modalApiKey || apiKeyActiva;
      const response = await fetch(
        `https://api.lula.com/v1/contact_lists/${listId}/contacts`,
        {
          headers: {
            accept: "application/json",
            "X-API-Key": key,
          },
        }
      );
      if (!response.ok)
        throw new Error(
          `Error ${response.status} al obtener contactos de la lista`
        );
      const contactsData = await response.json();
      setContactsInList(contactsData);
      setContactsInListModalVisible(true);
    } catch (error) {
      console.error("Error al obtener contactos de la lista:", error);
      notification.error({
        message: `Error al obtener contactos de la lista: ${error.message}`,
      });
    } finally {
      setLoadingContacts(false);
    }
  };

  const fetchRedialingRules = async () => {
    try {
      console.log("API Key Activa para el país:", apiKeyActiva);

      const response = await fetch("https://api.lula.com/v1/redialing_rules", {
        headers: {
          accept: "application/json",
          "X-API-Key": apiKeyActiva,
        },
      });

      if (!response.ok)
        throw new Error(
          `Error ${response.status} al obtener reglas de remarcado`
        );

      const allRules = await response.json();
      console.log(
        "Todas las reglas de remarcado para",
        paisSeleccionado,
        ":",
        allRules
      );

      setRedialingRules(allRules || []);
      setFilteredRedialingRules(allRules || []);
    } catch (error) {
      console.error("Error al obtener reglas de remarcado:", error);
      notification.error({
        message: `Error al obtener reglas de remarcado: ${error.message}`,
      });
    }
  };

  const fetchRedialingRuleDetails = async (ruleId) => {
    setLoadingRedialingRuleDetails(true);
    try {
      const response = await fetch(
        `https://api.lula.com/v1/redialing_rules/${ruleId}`,
        {
          headers: {
            accept: "text/plain",
            "X-API-Key": apiKeyActiva,
          },
        }
      );
      if (!response.ok)
        throw new Error(
          `Error ${response.status} al obtener detalles de la regla`
        );
      const ruleDetails = await response.json();
      setCurrentRedialingRuleDetails(ruleDetails);
      setRedialingRuleDetailModalVisible(true);
    } catch (error) {
      console.error(
        "Error al obtener detalles de la regla de remarcado:",
        error
      );
      notification.error({
        message: `Error al obtener detalles de la regla: ${error.message}`,
      });
    } finally {
      setLoadingRedialingRuleDetails(false);
    }
  };

  const fetchCampanas = async () => {
    try {
      const responseBackend = await fetch(
        `${API_URL_GATEWAY}/gateway/campanas/dar`
      );
      const backendData = await responseBackend.json();

      const gailCampaigns = [];
      for (const country of Object.keys(API_KEYS_BY_COUNTRY)) {
        try {
          const apiKey = API_KEYS_BY_COUNTRY[country];
          const response = await fetch("https://api.lula.com/v1/campaigns", {
            headers: {
              "X-API-Key": apiKey,
              accept: "application/json",
            },
          });

          if (response.ok) {
            const data = await response.json();
            gailCampaigns.push(
              ...data.map((c) => ({
                ...c,
                idCampana: c.id,
                descripcionCampana: c.name,
                origen: "Gail",
                pais: country,
              }))
            );
          }
        } catch (error) {
          console.error(`Error obteniendo campañas de ${country}`, error);
        }
      }

      const campañasBackend = backendData.map((c) => ({
        ...c,
        origen: "Aplicativo",
        pais: "N/A",
      }));

      setData([...campañasBackend, ...gailCampaigns]);
    } catch (error) {
      console.error("Error al obtener campañas:", error);
      notification.error({
        message: `Error al obtener campañas: ${error.message}`,
      });
    }
  };

  const fetchSequences = async () => {
    try {
      const activeResponse = await fetch(
        "https://api.lula.com/v1/sequences?status=active",
        {
          headers: {
            accept: "text/plain",
            "X-API-Key": apiKeyActiva,
          },
        }
      );
      if (!activeResponse.ok)
        throw new Error(
          `Error ${activeResponse.status} al obtener secuencias activas`
        );
      const activeSequences = await activeResponse.json();

      const archivedResponse = await fetch(
        "https://api.lula.com/v1/sequences?status=archived",
        {
          headers: {
            accept: "text/plain",
            "X-API-Key": apiKeyActiva,
          },
        }
      );
      if (!archivedResponse.ok)
        throw new Error(
          `Error ${archivedResponse.status} al obtener secuencias archivadas`
        );
      const archivedSequences = await archivedResponse.json();

      const allSequences = [
        ...(activeSequences || []),
        ...(archivedSequences || []),
      ];
      setSequences(allSequences);
      setFilteredSequences(allSequences);
    } catch (error) {
      console.error("Error al obtener secuencias:", error);
      notification.error({
        message: `Error al obtener secuencias: ${error.message}`,
      });
    }
  };

  const fetchCampaignTouchpoints = async (campaignId, campaignName) => {
  setTouchpointsLoading(true);
  setCampaignTouchpoints([]);
  setCurrentCampaignForTouchpoints(campaignName);

  const headers = {
    accept: "application/json",
    "X-API-Key": apiKeyActiva,
    "Content-Type": "application/json",
  };

  const SIZE = 10000; 
  let page = 1;
  const all = [];

  const fetchPage = async (p) => {
    const url = `https://api.lula.com/v1/campaigns/${campaignId}/touchpoints?includeTranscripts=true&page=${p}&size=${SIZE}`;
    const res = await fetch(url, { headers });
    if (res.status === 429 || res.status >= 500) {
      await new Promise((r) => setTimeout(r, 1000));
      return fetchPage(p);
    }
    if (!res.ok) throw new Error(`Error ${res.status} al obtener touchpoints (página ${p})`);
    return res.json();
  };

  try {
    while (true) {
      const result = await fetchPage(page);
      const batch = result?.data ?? result?.results ?? [];
      if (!Array.isArray(batch) || batch.length === 0) break;

      all.push(...batch);

      if (batch.length < SIZE) break;
      page += 1;
    }

    setCampaignTouchpoints(all);
    setTouchpointsModalVisible(true);
  } catch (error) {
    console.error("Error al obtener touchpoints de la campaña:", error);
    notification.error({
      message: `Error al obtener touchpoints: ${error.message}`,
    });
  } finally {
    setTouchpointsLoading(false);
  }
};


  const processTouchpointsForChart = (touchpoints) => {
    const outcomeCounts = {};
    touchpoints.forEach((tp) => {
      outcomeCounts[tp.outcome] = (outcomeCounts[tp.outcome] || 0) + 1;
    });

    const labels = Object.keys(outcomeCounts);
    const data = Object.values(outcomeCounts);
    const backgroundColors = [
      "rgba(255, 99, 132, 0.6)", // Red
      "rgba(54, 162, 235, 0.6)", // Blue
      "rgba(255, 206, 86, 0.6)", // Yellow
      "rgba(75, 192, 192, 0.6)", // Green
      "rgba(153, 102, 255, 0.6)", // Purple
      "rgba(255, 159, 64, 0.6)", // Orange
    ];
    const borderColors = [
      "rgba(255, 99, 132, 1)",
      "rgba(54, 162, 235, 1)",
      "rgba(255, 206, 86, 1)",
      "rgba(75, 192, 192, 1)",
      "rgba(153, 102, 255, 1)",
      "rgba(255, 159, 64, 1)",
    ];

    return {
      labels,
      datasets: [
        {
          label: "# de Touchpoints",
          data,
          backgroundColor: labels.map(
            (_, i) => backgroundColors[i % backgroundColors.length]
          ),
          borderColor: labels.map(
            (_, i) => borderColors[i % backgroundColors.length]
          ),
          borderWidth: 1,
        },
      ],
    };
  };

  const handleDownloadTouchpointsExcel = (touchpoints, campaignName) => {
    if (!touchpoints?.length) {
      notification.info({ message: "No hay datos para exportar." });
      return;
    }
    const formatted = touchpoints.map((tp) => ({
      "First Name": tp.contactFirstName || "",
      "Last Name": tp.contactLastName || "",
      "Phone Number": tp.phoneNumber || "",
      Outcome: tp.outcome || "",
      Duration: tp.duration != null ? tp.duration : "",
      "Started Date": tp.publishedAt
        ? new Date(tp.publishedAt).toLocaleString()
        : "",
      "Finished Date": tp.finishedAt
        ? new Date(tp.finishedAt).toLocaleString()
        : "",

      "Failed Reason": tp.errorMessage || "",
      Transcript: (tp.transcript || [])
        .map((l) => `${l.role}: ${l.content}`)
        .join("\n"),
    }));

    const headers = [
      "First Name",
      "Last Name",
      "Phone Number",
      "Outcome",
      "Duration",
      "Started Date",
      "Finished Date",
      "Failed Reason",
      "Transcript",
    ];

    const ws = XLSX.utils.json_to_sheet(formatted, { header: headers });
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Touchpoints");
    const buf = XLSX.write(wb, { bookType: "xlsx", type: "array" });

    saveAs(
      new Blob([buf]),
      `Touchpoints_${campaignName.replace(/\s+/g, "_")}.xlsx`
    );

    notification.success({ message: "Archivo Excel descargado exitosamente." });
  };

  useEffect(() => {
    if (searchSequence) {
      setFilteredSequences(
        availableSequences.filter(
          (seq) =>
            seq.name &&
            seq.name.toLowerCase().includes(searchSequence.toLowerCase())
        )
      );
    } else {
      setFilteredSequences(availableSequences);
    }
  }, [searchSequence, availableSequences]);

  useEffect(() => {
    if (searchContactList) {
      setFilteredContactLists(
        availableContactLists.filter(
          (list) =>
            list.name &&
            list.name.toLowerCase().includes(searchContactList.toLowerCase())
        )
      );
    } else {
      setFilteredContactLists(availableContactLists);
    }
  }, [searchContactList, availableContactLists]);

  useEffect(() => {
    if (searchRedialingRule) {
      setFilteredRedialingRules(
        availableRules.filter(
          (rule) =>
            rule.name &&
            rule.name.toLowerCase().includes(searchRedialingRule.toLowerCase())
        )
      );
    } else {
      setFilteredRedialingRules(availableRules);
    }
    console.log("Cargando reglas para el modal");
  }, [searchRedialingRule, availableRules]);

  const editSequence = async (record) => {
    if (!apiKeyActiva) {
      notification.error({
        message:
          "No hay API Key activa seleccionada. Selecciona un país primero.",
      });
      return;
    }
    try {
      await fetchScripts(modalApiKey || apiKeyActiva);

      const response = await fetch(
        `https://api.lula.com/v1/sequences/${record.id}`,
        {
          headers: {
            "X-API-Key": modalApiKey || apiKeyActiva,
            accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error(
          "Error al obtener secuencia completa:",
          response.status,
          errorText
        );
        throw new Error(`Error ${response.status}: ${errorText}`);
      }

      const data = await response.json();

      setEditingSequence(data);

      form.setFieldsValue({
        name: data.name,
        description: data.description,
        criteria: data.criteria,
        status: data.status,
        timezone: data.timezone,
        schedules: data.schedules.map((s) => {
          return {
            dayOffset: s.dayOffset,
            delayInMinutes: s.delayInMinutes,
            time: moment().hour(s.hour).minute(s.minute),
            sequenceScripts: s.scripts?.map((sc) => sc.id) || [],
          };
        }),
      });

      setEditSequenceModalVisible(true);
    } catch (error) {
      console.error("Error al obtener secuencia completa:", error);
      notification.error({ message: "No se pudo cargar la secuencia" });
    }
  };

  const handleUpdateSequence = async () => {
    try {
      const values = await form.validateFields();

      if (!values.schedules || values.schedules.length === 0) {
        notification.error({
          message: "Debe agregar al menos un horario (schedule).",
        });
        return;
      }

      const transformedSchedules = values.schedules.map((s) => {
        const scriptIds = Array.isArray(s.sequenceScripts)
          ? s.sequenceScripts.map((sc) =>
              typeof sc === "object" ? sc.value || sc.id : sc
            )
          : [];

        if (scriptIds.length === 0) {
          throw new Error(
            "Cada horario debe tener al menos un Script ID asignado."
          );
        }

        const hour = s.time.hour();
        const minute = s.time.minute();

        return {
          dayOffset: s.dayOffset,
          delayInMinutes: s.delayInMinutes,
          hour,
          minute,
          sequenceScripts: scriptIds,
        };
      });

      const payload = {
        name: values.name,
        description: values.description,
        criteria: "true",
        timezone: values.timezone,
        schedules: transformedSchedules,
      };

      console.log("Payload enviado a Lula:", JSON.stringify(payload, null, 2));

      const response = await fetch(
        `https://api.lula.com/v1/sequences/${editingSequence.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": modalApiKey || apiKeyActiva,
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: "Error al procesar la respuesta del servidor.",
        }));
        throw new Error(
          errorData.message ||
            `Error ${response.status} al actualizar la secuencia`
        );
      }

      notification.success({ message: "Secuencia actualizada correctamente" });
      setEditSequenceModalVisible(false);
      setEditingSequence(null);
      form.resetFields();
      fetchSequences();
    } catch (errorInfo) {
      console.error("Error en handleUpdateSequence:", errorInfo);
      let errorMessage = "Error al actualizar la secuencia.";
      if (errorInfo.message) {
        errorMessage = errorInfo.message;
      } else if (errorInfo.errorFields) {
        errorMessage = "Por favor revise los campos del formulario.";
      }
      notification.error({ message: errorMessage });
    }
  };

  const archiveSequence = async (id) => {
    try {
      const response = await fetch(
        `https://api.lula.com/v1/sequences/${id}/archive`,
        {
          method: "POST",
          headers: {
            "X-API-Key": modalApiKey || apiKeyActiva,
          },
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: "Error al procesar la respuesta del servidor.",
        }));
        throw new Error(
          errorData.message ||
            `Error ${response.status} al archivar la secuencia`
        );
      }
      notification.success({ message: "Secuencia archivada exitosamente" });
      fetchSequences();
    } catch (error) {
      console.error("Error en archiveSequence:", error);
      notification.error({
        message: error.message || "Error al archivar la secuencia",
      });
    }
  };

  const restoreSequence = async (id) => {
    try {
      const response = await fetch(
        `https://api.lula.com/v1/sequences/${id}/restore`,
        {
          method: "POST",
          headers: {
            "X-API-Key": modalApiKey || apiKeyActiva,
          },
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: "Error al procesar la respuesta del servidor.",
        }));
        throw new Error(
          errorData.message ||
            `Error ${response.status} al restaurar la secuencia`
        );
      }
      notification.success({ message: "Secuencia restaurada exitosamente" });
      fetchSequences();
    } catch (error) {
      console.error("Error en restoreSequence:", error);
      notification.error({
        message: error.message || "Error al restaurar la secuencia",
      });
    }
  };

  const getColumnSearchProps = (dataIndex) => ({
    filterDropdown: ({
      setSelectedKeys,
      selectedKeys,
      confirm,
      clearFilters,
    }) => (
      <div style={{ padding: 8 }}>
        <Input
          placeholder={`Buscar ${dataIndex}`}
          value={selectedKeys[0]}
          onChange={(e) =>
            setSelectedKeys(e.target.value ? [e.target.value] : [])
          }
          onPressEnter={() => handleSearch(selectedKeys, confirm, dataIndex)}
          style={{ marginBottom: 8, display: "block" }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm, dataIndex)}
            icon={<SearchOutlined />}
            size="small"
          >
            Buscar
          </Button>
          <Button onClick={() => handleReset(clearFilters)} size="small">
            Limpiar
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered) => (
      <SearchOutlined style={{ color: filtered ? "#1890ff" : undefined }} />
    ),
    onFilter: (value, record) =>
      record[dataIndex]?.toString().toLowerCase().includes(value.toLowerCase()),
    render: (text) =>
      searchedColumn === dataIndex ? (
        <span style={{ backgroundColor: "#ffc069", padding: 0 }}>{text}</span>
      ) : (
        text
      ),
  });

  const handleSearch = (selectedKeys, confirm, dataIndex) => {
    confirm();
    setSearchTextGlobal(selectedKeys[0]);
    setSearchedColumn(dataIndex);
  };

  const handleReset = (clearFilters) => {
    clearFilters();
    setSearchTextGlobal("");
  };

  const handleCreateContactList = async () => {
    try {
      if (!newContactListName) {
        notification.error({
          message: "El nombre de la lista de contacto no puede estar vacío.",
        });
        return;
      }

      const payload = {
        name: newContactListName,
        description: newContactListDescription,
      };

      const key = modalApiKey || apiKeyActiva;

      const response = await fetch("https://api.lula.com/v1/contact_lists", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": key,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: "Error al procesar la respuesta del servidor.",
        }));
        throw new Error(
          errorData.message ||
            `Error ${response.status} al crear la lista de contacto`
        );
      }

      const newList = await response.json();

      setAvailableContactLists((prev) => [...prev, newList]);
      setFilteredContactLists((prev) => [...prev, newList]);

      setAvailableContactListsModal((prev) => [...prev, newList]);

      notification.success({
        message: "Lista de contacto creada exitosamente",
      });
      setCreateContactListModalVisible(false);
      setNewContactListName("");
      setNewContactListDescription("");
    } catch (error) {
      console.error("Error en handleCreateContactList:", error);
      notification.error({
        message: error.message || "Error al crear la lista de contacto",
      });
    }
  };

  const handleCreateNewSequence = async () => {
    try {
      const values = await form.validateFields();
      const apiKey = modalApiKey || apiKeyActiva;

      if (!values.schedules || values.schedules.length === 0) {
        notification.error({
          message: "Debe agregar al menos un horario (schedule).",
        });
        return;
      }

      const transformedSchedules = values.schedules.map((s) => {
        const scriptIds = Array.isArray(s.sequenceScripts)
          ? s.sequenceScripts.map((sc) =>
              typeof sc === "object" ? sc.value || sc.id : sc
            )
          : [];

        if (scriptIds.length === 0) {
          throw new Error(
            "Cada horario debe tener al menos un Script ID asignado."
          );
        }

        const hour = s.hour;
        const minute = s.minute;

        return {
          dayOffset: s.dayOffset,
          delayInMinutes: s.delayInMinutes,
          hour,
          minute,
          sequenceScripts: scriptIds,
        };
      });

      const availableScriptIds = scriptOptions.map((opt) => opt.value);
      transformedSchedules.forEach((schedule) => {
        schedule.sequenceScripts.forEach((scriptId) => {
          if (!availableScriptIds.includes(scriptId)) {
            throw new Error(
              `Script ID inválido: ${scriptId}. No está disponible en Lula.`
            );
          }
        });
      });

      const payload = {
        name: values.name,
        description: values.description,
        criteria: "true",
        timezone: values.timezone,
        schedules: transformedSchedules,
      };

      console.log("Payload enviado a Lula:", JSON.stringify(payload, null, 2));

      const response = await fetch(`https://api.lula.com/v1/sequences`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const responseText = await response.text();
        console.error("Respuesta completa de error:", responseText);
        let errorData;
        try {
          errorData = JSON.parse(responseText);
        } catch (err) {
          errorData = { message: responseText };
        }
        throw new Error(
          errorData.message || `Error ${response.status} al crear la secuencia`
        );
      }

      notification.success({ message: "Secuencia creada correctamente" });
      setCreateSequenceModalVisible(false);
      form.resetFields();
      fetchSequences();

      const newSequence = await response.json();

      setSequences((prev) => [...prev, newSequence]);
      setFilteredSequences((prev) => [...prev, newSequence]);
      setAvailableSequences((prev) => [...prev, newSequence]);

      if (modalApiKey) {
        setAvailableSequencesModal((prev) => [...prev, newSequence]);
      }

      notification.success({ message: "Secuencia creada correctamente" });
      setCreateSequenceModalVisible(false);
      form.resetFields();
    } catch (errorInfo) {
      console.error("Error en handleCreateNewSequence:", errorInfo);
      let errorMessage = "Error al crear la secuencia.";
      if (errorInfo.message) {
        errorMessage = errorInfo.message;
      } else if (errorInfo.errorFields) {
        errorMessage = "Por favor revise los campos del formulario.";
      }
      notification.error({ message: errorMessage });
    }
  };

  const archiveContactList = async (id) => {
    try {
      const response = await fetch(
        `https://api.lula.com/v1/contact_lists/${id}/archive`,
        {
          method: "POST",
          headers: {
            "X-API-Key": apiKeyActiva,
          },
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: "Error al procesar la respuesta del servidor.",
        }));
        throw new Error(
          errorData.message ||
            `Error ${response.status} al archivar la lista de contacto`
        );
      }
      notification.success({
        message: "Lista de contacto archivada exitosamente",
      });
      fetchContactLists();
    } catch (error) {
      console.error("Error en archiveContactList:", error);
      notification.error({
        message: error.message || "Error al archivar la lista de contacto",
      });
    }
  };

  const restoreContactList = async (id) => {
    try {
      const response = await fetch(
        `https://api.lula.com/v1/contact_lists/${id}/restore`,
        {
          method: "POST",
          headers: {
            "X-API-Key": apiKeyActiva,
          },
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: "Error al procesar la respuesta del servidor.",
        }));
        throw new Error(
          errorData.message ||
            `Error ${response.status} al restaurar la lista de contacto`
        );
      }
      notification.success({
        message: "Lista de contacto restaurada exitosamente",
      });
      fetchContactLists();
    } catch (error) {
      console.error("Error en restoreContactList:", error);
      notification.error({
        message: error.message || "Error al restaurar la lista de contacto",
      });
    }
  };

  const handleAddContact = (listId) => {
    setSelectedContactListForAddingContact(listId);
    setAddContactModalVisible(true);
    addContactForm.resetFields();
    addContactForm.setFieldsValue({
      additionalData: defaultAdditionalDataFields,
    });
  };

  const handleSaveContact = async () => {
    try {
      const values = await addContactForm.validateFields();

      if (!values.phoneNumbers || values.phoneNumbers.length === 0) {
        throw new Error("Debes ingresar al menos un número de teléfono.");
      }

      const invalidNumber = values.phoneNumbers.find(
        (p) => !p.number.startsWith("+")
      );
      if (invalidNumber) {
        throw new Error(
          "El número debe incluir el código de país con +, por ejemplo: +573001234567"
        );
      }
      const additionalData = values.additionalData
        ? values.additionalData.reduce((acc, item) => {
            if (item.key && item.value && item.value.trim() !== "") {
              acc[item.key] = item.value;
            }
            return acc;
          }, {})
        : {};

      const payload = {
        requests: bulkContacts.map((contact) => ({
          firstName: contact.firstName,
          lastName: contact.lastName,
          businessName: contact.businessName
            ? String(contact.businessName)
            : "",
          emails: contact.emails,
          phoneNumbers: contact.phoneNumbers,
          additionalData: contact.additionalData,
        })),
      };

      const key = modalApiKey || apiKeyActiva;
      const createResponse = await fetch(
        "https://api.lula.com/v1/contacts/bulk_add",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": key,
          },
          body: JSON.stringify(payload),
        }
      );

      const createdContacts = await createResponse.json();

      if (!createResponse.ok || createdContacts.succeeded === 0) {
        const firstError =
          createdContacts.results?.[0]?.errors?.[0]?.message ||
          "Error desconocido";
        console.error("❌ Error en bulk_add:", firstError);
        throw new Error(`Error creando contacto: ${firstError}`);
      }

      const createdContactId = createdContacts.results?.[0]?.id;
      if (!createdContactId) {
        console.error(
          "❌ No se obtuvo el ID del contacto creado:",
          createdContacts
        );
        throw new Error("No se pudo obtener el ID del contacto creado.");
      }

      const associateResponse = await fetch(
        `https://api.lula.com/v1/contact_lists/${selectedContactListForAddingContact}/add`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": key,
          },
          body: JSON.stringify({ contactIds: [createdContactId] }),
        }
      );

      if (!associateResponse.ok) {
        const errorText = await associateResponse.text();
        console.error("❌ Error al asociar contacto a lista:", errorText);
        throw new Error(`Error asociando contacto a la lista: ${errorText}`);
      }

      notification.success({ message: "Contacto añadido exitosamente" });
      setAddContactModalVisible(false);
      fetchContactsInList(selectedContactListForAddingContact);
    } catch (error) {
      console.error("Error en handleSaveContact:", error);
      notification.error({
        message: error.message || "Error al añadir contacto",
      });
    }
  };

  const handleAddBackendCampaign = () => {
    setNewDescripcion("");
    setSelectedCampaignId(null);
    setModalVisible(true);
  };

  const handleEditBackendCampaign = (record) => {
    setSelectedCampaignId(record.idCampana);
    setNewDescripcion(record.descripcionCampana);
    setSelectedSequence(null);
    setSelectedContactList(null);
    setSelectedRedialingRule(null);
    setSelectedCampaignName(record.descripcionCampana);
    setModalVisible(true);
  };

  const handleDeleteBackendCampaign = async (idCampana) => {
    try {
      const response = await fetch(
        `${API_URL_GATEWAY}/gateway/campanas/eliminar`,
        {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idCampana }),
        }
      );

      if (response.ok) {
        notification.success({ message: "Campaña eliminada exitosamente" });
        fetchCampanas();
      } else {
        throw new Error("Error al eliminar la campaña");
      }
    } catch (error) {
      console.error("Error al eliminar campaña:", error);
      notification.error({ message: "Error al eliminar campaña" });
    }
  };

  const handleSaveBackendCampaign = async () => {
    try {
      if (!newDescripcion) {
        notification.error({ message: "La descripción no puede estar vacía." });
        return;
      }

      const payload = {
        descripcionCampana: newDescripcion,
        ...(selectedCampaignId && { idCampana: selectedCampaignId }),
      };

      const url = selectedCampaignId
        ? `${API_URL_GATEWAY}/gateway/campanas/editar`
        : `${API_URL_GATEWAY}/gateway/campanas/crear`;

      const method = selectedCampaignId ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        notification.success({
          message: selectedCampaignId
            ? "Campaña actualizada exitosamente"
            : "Campaña creada exitosamente",
        });
        setModalVisible(false);
        fetchCampanas();
      } else {
        throw new Error("Error al guardar en el backend");
      }
    } catch (error) {
      console.error("Error al guardar campaña:", error);
      notification.error({ message: "No se pudo guardar la campaña" });
    }
  };

  const handleCancelBackendCampaignModal = () => {
    setModalVisible(false);
  };

  const handleOpenLulaCreateModal = (record) => {
    setModoCreacionLibre(false);
    setSelectedCampaignName(record.descripcionCampana);
    setNewDescripcion(record.descripcionCampana);
    setSelectedCampaignId(record.idCampana);
    setSelectedSequence(record.sequence.id);
    setSelectedContactList(record.contactList.id);
    setSelectedRedialingRule(record.redialingRule.id);
    setModalCountry(record.pais);
    setModalApiKey(API_KEYS_BY_COUNTRY[record.pais]);
    setLulaCreateModalVisible(true);
  };

  const handleSaveLulaCampaign = async () => {
    const campaignNameToUse = newDescripcion || selectedCampaignName;

    if (
      !selectedSequence ||
      !selectedContactList ||
      !selectedRedialingRule ||
      !campaignNameToUse
    ) {
      notification.error({ message: "Todos los campos son obligatorios" });
      return;
    }
    const contactList = availableContactListsModal.find(
      (l) => l.id === selectedContactList
    );
    const sequence = availableSequencesModal.find(
      (s) => s.id === selectedSequence
    );
    const redialingRule = availableRulesModal.find(
      (r) => r.id === selectedRedialingRule
    );

    const contactListPayload = {
      id: contactList.id,
      name: contactList.name,
      description: contactList.description || "",
    };

    if (!contactList || !sequence || !redialingRule) {
      notification.error({
        message: "Uno o más recursos seleccionados no son válidos",
      });
      return;
    }
    if (!modalCountry) {
      notification.error({ message: "Debes seleccionar un país." });
      return;
    }

    setCreatingCampaign(true);

    try {
      const sequenceDetails = sequences.find((s) => s.id === selectedSequence);
      const contactListDetails = contactLists.find(
        (c) => c.id === selectedContactList
      );
      const redialingRuleDetails = redialingRules.find(
        (r) => r.id === selectedRedialingRule
      );

      if (sequenceDetails?.status !== "active") {
        console.warn(
          `⚠️ La secuencia está en estado: ${sequenceDetails?.status}`
        );
      }
      if (contactListDetails?.status !== "active") {
        console.warn(
          `⚠️ La lista de contactos está en estado: ${contactListDetails?.status}`
        );
      }
      if (redialingRuleDetails?.status !== "active") {
        console.warn(
          `⚠️ La regla de remarcado está en estado: ${redialingRuleDetails?.status}`
        );
      }

      const uuidRegex =
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
      if (!uuidRegex.test(selectedSequence)) {
        console.error(
          "❌ Formato de UUID inválido para secuencia:",
          selectedSequence
        );
      }
      if (!uuidRegex.test(selectedContactList)) {
        console.error(
          "❌ Formato de UUID inválido para lista de contactos:",
          selectedContactList
        );
      }
      if (!uuidRegex.test(selectedRedialingRule)) {
        console.error(
          "❌ Formato de UUID inválido para regla de remarcado:",
          selectedRedialingRule
        );
      }

      const campaignData = {
        name: campaignNameToUse,
        description: campaignNameToUse,
        status: "inactive",
        timezone: "America/Bogota",
        sequences: [{ sequenceId: selectedSequence, rank: 0 }],
        contactLists: [contactListPayload],
        redialingRules: selectedRedialingRule,
        criteria: { source: "auto" },
      };
      console.log(
        "Payload enviado a Lula:",
        JSON.stringify(campaignData, null, 2)
      );

      const alternativeCampaignData = {
        name: selectedCampaignName,
        description: newDescripcion || selectedCampaignName,
        status: "active",
        timezone: "America/Bogota",
        sequences: [{ sequenceId: selectedSequence, rank: 0 }],
        contactLists: [contactListPayload],
        redialingRules: selectedRedialingRule,
        criteria: { source: "auto" },
      };

      console.log(
        "Payload alternativo preparado:",
        JSON.stringify(alternativeCampaignData, null, 2)
      );

      const lulaResponse = await fetch("https://api.lula.com/v1/campaigns", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": modalApiKey,
          accept: "application/json",
        },
        body: JSON.stringify(campaignData),
      });

      if (!lulaResponse.ok) {
        const responseText = await lulaResponse.text();
        const responseDetails = {
          status: lulaResponse.status,
          statusText: lulaResponse.statusText,
          url: lulaResponse.url,
          headers: Object.fromEntries(lulaResponse.headers.entries()),
          bodyText: responseText,
          bodyLength: responseText ? responseText.length : 0,
        };

        console.error("=== RESPUESTA COMPLETA DE LULA ===");
        console.error(JSON.stringify(responseDetails, null, 2));
        console.error("=== FIN RESPUESTA LULA ===");

        let errorMessage = `Error ${lulaResponse.status}: ${lulaResponse.statusText}`;
        let errorDetails = null;

        if (responseText && responseText.trim().length > 0) {
          try {
            const errorData = JSON.parse(responseText);
            console.error("Error parseado como JSON:", errorData);

            errorMessage =
              errorData.message ||
              errorData.error ||
              errorData.detail ||
              errorMessage;
            errorDetails = errorData;

            if (errorData.details) {
              console.error("Detalles del error:", errorData.details);
            }
            if (errorData.validation_errors) {
              console.error(
                "Errores de validación:",
                errorData.validation_errors
              );
            }
            if (errorData.errors) {
              console.error("Lista de errores:", errorData.errors);
            }
          } catch (parseError) {
            console.error("No se pudo parsear como JSON:", parseError.message);
            console.error("Respuesta raw:", responseText);
          }
        } else {
          console.error("Respuesta vacía del servidor");
          errorMessage = `Error ${lulaResponse.status}: Respuesta vacía del servidor`;
        }

        throw new Error(errorMessage);
      }

      const lulaCampaign = await lulaResponse.json();
      const lulaCampaignId = lulaCampaign.id;

      const key = modalApiKey || apiKeyActiva;
      const contactsResponse = await fetch(
        `https://api.lula.com/v1/contact_lists/${selectedContactList}/contacts`,
        { headers: { "X-API-Key": key, accept: "application/json" } }
      );

      if (!contactsResponse.ok) {
        console.warn(
          "No se pudieron obtener los contactos, continuando sin ellos"
        );
      }

      const contactsData = contactsResponse.ok
        ? await contactsResponse.json()
        : { data: [] };

      const backendPayload = {
        idCampana: lulaCampaignId,
        name: selectedCampaignName,
        description: newDescripcion || selectedCampaignName,
        status: "active",
        timezone: "America/Bogota",
        pais: modalCountry,

        contactList: {
          id: contactList.id,
          name: contactList.name,
          description: contactList.description || "",
        },
        sequence: {
          id: sequence.id,
          name: sequence.name,
          description: sequence.description || "",
        },
        redialingRule: {
          id: redialingRule.id,
          name: redialingRule.name,
          outcomes: redialingRule.outcomes || [],
          systemActions: redialingRule.systemActions || {},
        },
        contactos: (contactsData.data || []).map((c) => ({
          id: c.id,
          firstName: c.firstName,
          lastName: c.lastName,
          businessName: c.businessName,
          source: c.source,
          status: c.status,
          phoneNumbers: c.phoneNumbers,
          additionalData: c.additionalData,
        })),
      };

      console.log(
        "Payload enviado al backend:",
        JSON.stringify(backendPayload, null, 2)
      );

      const backendResponse = await fetch(
        `${API_URL_GATEWAY}/gateway/campanas/registrar-gail`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(backendPayload),
        }
      );

      if (!backendResponse.ok) {
        const errorText = await backendResponse.text();
        console.error("Error del backend:", errorText);
        throw new Error(`Error registrando en base de datos: ${errorText}`);
      }

      notification.success({
        message:
          "Campaña creada en Lula y registrada en base de datos exitosamente",
      });
      setLulaCreateModalVisible(false);
      fetchCampanas();
    } catch (error) {
      console.error("Error completo al crear campaña:", error);
      notification.error({
        message: `Error al crear campaña: ${error.message}`,
        description: "Revisa la consola para más detalles",
      });
    } finally {
      setCreatingCampaign(false);
    }
  };

  const renderGailActions = (record) => {
    const estado = record.status.toLowerCase();
    const puedeIniciarse = estado !== "active";
    const puedeDetener = estado === "active";

    return (
      <Space>
        {puedeIniciarse && (
          <Tooltip title="Iniciar">
            <Button
              shape="circle"
              icon={<PlayCircleOutlined />}
              onClick={() => startGailCampaign(record)}
            />
          </Tooltip>
        )}

        {puedeDetener && (
          <Tooltip title="Finalizar">
            <Button
              danger
              shape="circle"
              icon={<PauseCircleOutlined />}
              onClick={() => stopGailCampaign(record)}
            />
          </Tooltip>
        )}

        <Tooltip title="Resultados">
          <Button
            icon={<EyeOutlined />}
            onClick={() =>
              fetchCampaignTouchpoints(
                record.idCampana,
                record.descripcionCampana
              )
            }
          />
        </Tooltip>
      </Space>
    );
  };

  const filteredData = data.filter((item) => {
    const matchesOrigen =
      selectedOrigenFilter === "todos" || item.origen === selectedOrigenFilter;
    const matchesSearch = item.descripcionCampana
      ?.toLowerCase()
      .includes(searchTextGlobal.toLowerCase());
    const matchesCountry =
      item.origen === "Aplicativo" ||
      !paisSeleccionado ||
      item.pais === paisSeleccionado;

    return matchesOrigen && matchesSearch && matchesCountry;
  });

  const columns = [
    {
      title: "Campaña",
      dataIndex: "descripcionCampana",
      key: "descripcionCampana",
      ...getColumnSearchProps("descripcionCampana"),
    },
    {
      title: "Origen",
      dataIndex: "origen",
      key: "origen",
      ...getColumnSearchProps("origen"),
      render: (origen) => (
        <Tag color={origen === "Gail" ? "blue" : "green"}>{origen}</Tag>
      ),
    },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => {
        if (record.origen === "Aplicativo") {
          return (
            <Space>
              <Tooltip title="Editar campaña backend">
                <Button
                  shape="circle"
                  icon={<EditOutlined />}
                  onClick={() => handleEditBackendCampaign(record)}
                />
              </Tooltip>

              <Tooltip title="Eliminar campaña backend">
                <Button
                  danger
                  shape="circle"
                  icon={<DeleteOutlined />}
                  onClick={() => handleDeleteBackendCampaign(record.idCampana)}
                />
              </Tooltip>

              <Tooltip title="Crear en Gail">
                <Button
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setModoCreacionLibre(true);
                    setNewDescripcion("");
                    setSelectedSequence(null);
                    setSelectedContactList(null);
                    setSelectedRedialingRule(null);
                    setSelectedCountry(null);
                    setLulaCreateModalVisible(true);
                  }}
                >
                  Crear en Gail
                </Button>
              </Tooltip>
            </Space>
          );
        }

        if (record.origen === "Gail") {
          return renderGailActions(record);
        }

        return null;
      },
    },
  ];

  const sequenceColumns = [
    {
      title: "Nombre",
      dataIndex: "name",
      key: "name",
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    { title: "Descripción", dataIndex: "description", key: "description" },
    { title: "Estado", dataIndex: "status", key: "status" },
    {
      title: "Acción",
      key: "action",
      render: (_, record) => (
        <Space>
          <Tooltip title="Editar Secuencia">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => editSequence(record)}
            >
              Editar
            </Button>
          </Tooltip>
          {record.status && record.status.toLowerCase() === "active" ? (
            <Tooltip title="Archivar Secuencia">
              <Button
                size="small"
                danger
                onClick={() => archiveSequence(record.id)}
              >
                Archivar
              </Button>
            </Tooltip>
          ) : record.status && record.status.toLowerCase() === "archived" ? (
            <Tooltip title="Restaurar Secuencia">
              <Button
                size="small"
                style={{
                  backgroundColor: "#52c41a",
                  borderColor: "#52c41a",
                  color: "white",
                }}
                onClick={() => restoreSequence(record.id)}
              >
                Restaurar
              </Button>
            </Tooltip>
          ) : (
            <Tooltip title="Estado Inactivo/Desconocido">
              <Button size="small" disabled>
                Acción no disponible
              </Button>
            </Tooltip>
          )}
          <Button
            type="primary"
            size="small"
            onClick={() => {
              setSelectedSequence(record.id);
              setSequencesManageModalVisible(false);
              notification.info({
                message: `Secuencia "${record.name}" seleccionada para la campaña Gail.`,
              });
            }}
          >
            Usar
          </Button>
        </Space>
      ),
    },
  ];

  const contactListColumns = [
    {
      title: "Nombre",
      dataIndex: "name",
      key: "name",
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    { title: "Descripción", dataIndex: "description", key: "description" },
    { title: "Estado", dataIndex: "status", key: "status" },
    {
      title: "Acción",
      key: "action",
      render: (_, record) => (
        <Space>
          <Tooltip title="Ver Contactos">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setCurrentContactListId(record.id);
                fetchContactsInList(record.id);
              }}
            >
              Ver Contactos
            </Button>
          </Tooltip>
          <Tooltip title="Añadir Contacto">
            <Button
              size="small"
              icon={<PlusOutlined />}
              onClick={() => handleAddContact(record.id)}
            >
              Añadir Contacto
            </Button>
          </Tooltip>
          {record.status && record.status.toLowerCase() === "active" ? (
            <Tooltip title="Archivar Lista de Contacto">
              <Button
                size="small"
                danger
                onClick={() => archiveContactList(record.id)}
              >
                Archivar
              </Button>
            </Tooltip>
          ) : record.status && record.status.toLowerCase() === "archived" ? (
            <Tooltip title="Restaurar Lista de Contacto">
              <Button
                size="small"
                style={{
                  backgroundColor: "#52c41a",
                  borderColor: "#52c41a",
                  color: "white",
                }}
                onClick={() => restoreContactList(record.id)}
              >
                Restaurar
              </Button>
            </Tooltip>
          ) : (
            <Tooltip title="Estado Inactivo/Desconocido">
              <Button size="small" disabled>
                Acción no disponible
              </Button>
            </Tooltip>
          )}
          <Button
            type="primary"
            size="small"
            onClick={() => {
              setSelectedContactList(record.id);
              setContactListsManageModalVisible(false);
              notification.info({
                message: `Lista de Contactos "${record.name}" seleccionada.`,
              });
            }}
          >
            Usar
          </Button>
        </Space>
      ),
    },
  ];

  const contactsInListTableColumns = [
    {
      title: "Nombre",
      dataIndex: "firstName",
      key: "firstName",
      render: (text, record) =>
        `${text || ""} ${record.lastName || ""}`.trim() || "N/A",
    },
    {
      title: "Teléfono",
      dataIndex: "phoneNumbers",
      key: "phoneNumbers",
      render: (phones) =>
        phones && phones.length > 0 ? phones[0].number : "N/A",
    },
    {
      title: "Outcome",
      dataIndex: "outcome",
      key: "outcome",
      render: (outcome) => outcome || "N/A",
    },
    {
      title: "Duración (s)",
      dataIndex: "duration",
      key: "duration",
      render: (duration) => duration || "N/A",
    },
    {
      title: "Transcripción",
      dataIndex: "transcript",
      key: "transcript",
      render: (transcript) =>
        transcript && transcript.length > 0 ? (
          <ul style={{ listStyleType: "none", paddingLeft: 0 }}>
            {transcript.map((item, idx) => (
              <li key={idx}>
                <strong>{item.role}:</strong> {item.content}
              </li>
            ))}
          </ul>
        ) : (
          "N/A"
        ),
    },
    {
      title: "Datos Adicionales",
      key: "additionalDataAction",
      render: (_, record) => {
        const additionalData = record.additionalData;
        const hasData =
          additionalData &&
          Object.values(additionalData).some(
            (value) => value !== null && value !== "" && value !== undefined
          );

        return hasData ? (
          <Tooltip title="Ver Datos Adicionales">
            <Button
              size="small"
              icon={<InfoCircleOutlined />}
              onClick={() => {
                setCurrentAdditionalData(additionalData);
                setAdditionalDataModalVisible(true);
              }}
            >
              Ver Detalles
            </Button>
          </Tooltip>
        ) : (
          "N/A"
        );
      },
    },
  ];

  const redialingRulesColumns = [
    {
      title: "Nombre",
      dataIndex: "name",
      key: "name",
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    { title: "Estado", dataIndex: "status", key: "status" },
    {
      title: "Máx Intentos",
      dataIndex: "outreachMaxAttempts",
      key: "outreachMaxAttempts",
    },
    {
      title: "Máx Intentos por Número",
      dataIndex: "outreachMaxAttemptsForNumber",
      key: "outreachMaxAttemptsForNumber",
    },
    {
      title: "Acción",
      key: "action",
      render: (_, record) => (
        <Space>
          <Tooltip title="Ver Detalles de Regla">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => fetchRedialingRuleDetails(record.id)}
            >
              Ver Detalles
            </Button>
          </Tooltip>
          <Button
            type="primary"
            size="small"
            onClick={() => {
              setSelectedRedialingRule(record.id);
              setRedialingRulesManageModalVisible(false);
              notification.info({
                message: `Regla de Remarcado "${record.name}" seleccionada.`,
              });
            }}
          >
            Usar
          </Button>
        </Space>
      ),
    },
  ];

  const resetLulaModalState = () => {
    setSelectedSequence(null);
    setSelectedContactList(null);
    setSelectedRedialingRule(null);
    setSelectedCampaignName("");
    setNewDescripcion("");
    setModalCountry(null);
    setModalApiKey(null);
  };

  const resetAvailableResources = () => {
    setAvailableSequences([]);
    setAvailableSequencesModal([]);
    setAvailableContactLists([]);
    setAvailableContactListsModal([]);
    setAvailableRules([]);
    setAvailableRulesModal([]);
  };

  const handleExcelUpload = (file) =>
    new Promise((resolve, reject) => {
      setLoadingExcel(true);
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: "array" });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { defval: "" });

          const formattedContacts = jsonData.map((row) => {
            const telefonoRaw = row["Teléfono"];
            return {
              firstName: row["Nombre"] ?? "",
              lastName: row["Nombre_Hmlg"] ?? "",
              businessName: row["Producto"] ?? "",
              emails: [],
              phoneNumbers: telefonoRaw
                ? [
                    {
                      number: `+${String(telefonoRaw).replace(/^(\+)?/, "")}`,
                      type: "mobile",
                    },
                  ]
                : [],
              additionalData: {
                Cedula: row["Cedula"] ?? "",
                Ciudad: row["Ciudad"] ?? "",
                Banco: row["Banco"] ?? "",
                "Ultimos digitos": row["Ultimos digitos"] ?? "",
                Capital: row["Capital"] ?? "",
                Producto: row["Producto"] ?? "",
                "Saldo total": row["Saldo total"] ?? "",
                "Oferta 1": row["Oferta 1"] ?? "",
                "Oferta 2": row["Oferta 2"] ?? "",
                "Oferta 3": row["Oferta 3"] ?? "",
                "Hasta 3 cuotas": row["Hasta 3 cuotas"] ?? "",
                "Hasta 6 cuotas": row["Hasta 6 cuotas"] ?? "",
                "Hasta 12 cuotas": row["Hasta 12 cuotas"] ?? "",
                "Pago Flexible": row["Pago Flexible"] ?? "",
                Inbound: row["Inbound"] ?? "",
                Genero: row["Genero"] ?? "",
                Intereses: row["Intereses"] ?? "",
                "Tipo Acuerdo": row["Tipo Acuerdo"] ?? "",
                "Valor de pago": row["Valor de pago"] ?? "",
                "Fecha de pago": row["Fecha de pago"] ?? "",
              },
            };
          });

          setBulkContacts(formattedContacts);
          notification.success({
            message: "Excel cargado correctamente",
            description: `${formattedContacts.length} contactos procesados.`,
          });
          resolve(formattedContacts);
        } catch (err) {
          notification.error({
            message: "Error al procesar el archivo Excel",
            description: err.message,
          });
          reject(err);
        } finally {
          setLoadingExcel(false);
        }
      };
      reader.onerror = (err) => {
        notification.error({
          message: "Error al leer el archivo",
          description: "No se pudo leer el archivo Excel",
        });
        setLoadingExcel(false);
        reject(err);
      };
      reader.readAsArrayBuffer(file);
    });

  const isDislicoresActive = () => {
    const key = (modalApiKey || apiKeyActiva || "").trim();
    return key === LULA_API_KEY_DISLICORES;
  };
  const handleExcelUploadDislicores = (file) =>
    new Promise((resolve, reject) => {
      setLoadingExcel(true);
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: "array" });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { defval: "" });

          const formattedContacts = jsonData.map((row) => {
            const telefonoRaw = row["Teléfono"];
            return {
              firstName: row["Nombre"] ?? "",
              lastName: row["Nombre"] ?? "",
              businessName: row["Nombre"] ?? "",
              emails: [],
              phoneNumbers: telefonoRaw
                ? [
                    {
                      number: `+${String(telefonoRaw).replace(/^(\+)?/, "")}`,
                      type: "mobile",
                    },
                  ]
                : [],
              additionalData: {
                "Nombre vendedor": row["Nombre vendedor"] ?? "",
                Supervisor: row["Supervisor"] ?? "",
                Dias: row["Dias"] ?? "",
                "Total COP": row["Total COP"] ?? "",
                "Oferta 1": row["Oferta 1"] ?? "",
                "Oferta 2": row["Oferta 2"] ?? "",
                "Cantidad de deudas": row["Cantidad de deudas"] ?? "",
                Factura_Convertida: row["Factura_Convertida"] ?? "",

                Factura: row["Factura"] ?? "",
                Cliente: row["Cliente"] ?? "",
                Sucursal: row["Sucursal"] ?? "",
                "Razón social": row["Razón social"] ?? "",
                "Razón social 01": row["Razón social 01"] ?? "",
                "Tipo docto cruce": row["Tipo docto cruce"] ?? "",
                Celular: row["Celular"] ?? "",
                "Dirección 1": row["Dirección 1"] ?? "",
                Ciudad: row["Ciudad"] ?? "",
                "Depto/Estado": row["Depto/Estado"] ?? "",
                "Desc. regional": row["Desc. regional"] ?? "",
                "Vendedor Actual": row["Vendedor Actual"] ?? "",
                "CANAL CLIENTE DISLICORES UN":
                  row["CANAL CLIENTE DISLICORES UN"] ?? "",
                SUBSEGMENTO: row["SUBSEGMENTO"] ?? "",
                "Cond. pago factura": row["Cond. pago factura"] ?? "",
                "Fecha docto.": row["Fecha docto."] ?? "",
                "Fecha vcto.": row["Fecha vcto."] ?? "",
                "Tipo edades": row["Tipo edades"] ?? "",
                "Nuevo telefono_x": row["Nuevo telefono_x"] ?? "",
                "Nuevo celular_x": row["Nuevo celular_x"] ?? "",
                "Nuevo telefono_y": row["Nuevo telefono_y"] ?? "",
                "Nuevo celular_y": row["Nuevo celular_y"] ?? "",
              },
            };
          });

          setBulkContacts(formattedContacts);
          notification.success({
            message: "Excel cargado correctamente",
            description: `${formattedContacts.length} contactos procesados.`,
          });
          resolve(formattedContacts);
        } catch (err) {
          notification.error({
            message: "Error al procesar el archivo Excel",
            description: err.message,
          });
          reject(err);
        } finally {
          setLoadingExcel(false);
        }
      };
      reader.onerror = (err) => {
        notification.error({
          message: "Error al leer el archivo",
          description: "No se pudo leer el archivo Excel",
        });
        setLoadingExcel(false);
        reject(err);
      };
      reader.readAsArrayBuffer(file);
    });

  const handleBulkAddContactsToList = async (listId, contactsParam) => {
    const contacts = contactsParam ?? bulkContacts;
    if (!contacts?.length) {
      notification.warning({ message: "No hay contactos cargados." });
      return;
    }
    try {
      const payload = contacts.map((contact) => ({
        firstName: contact.firstName,
        lastName: contact.lastName,
        businessName: contact.businessName ? String(contact.businessName) : "",
        emails: contact.emails,
        phoneNumbers: contact.phoneNumbers,
        additionalData: contact.additionalData,
      }));

      const key = modalApiKey || apiKeyActiva;

      const createResponse = await fetch(
        "https://api.lula.com/v1/contacts/bulk_add",
        {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": key },
          body: JSON.stringify(payload),
        }
      );
      const createdContacts = await createResponse.json();
      if (!createResponse.ok || createdContacts.succeeded === 0) {
        throw new Error(createdContacts.message || "Error creando contactos.");
      }

      const createdContactIds = createdContacts.results.map((r) => r.id);
      const associateResponse = await fetch(
        `https://api.lula.com/v1/contact_lists/${listId}/add`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": key },
          body: JSON.stringify({ contactIds: createdContactIds }),
        }
      );
      if (!associateResponse.ok) {
        const errorText = await associateResponse.text();
        throw new Error(`Error asociando contactos a la lista: ${errorText}`);
      }

      notification.success({
        message: "Contactos creados y asociados exitosamente",
      });
      setBulkContacts([]);
      fetchContactsInList(listId);
    } catch (error) {
      console.error("❌ Error en handleBulkAddContactsToList:", error);
      notification.error({
        message: error.message || "Error en creación masiva de contactos",
      });
    }
  };

  const handleDescargarPlantilla = async (nombrePlantilla) => {
    try {
      const response = await fetch(
        `${API_URL_GATEWAY}/gateway/campanas/descargar_plantilla?nombre=${nombrePlantilla}`
      );
      if (!response.ok) throw new Error("Error al descargar plantilla");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", nombrePlantilla);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (error) {
      console.error("Error al descargar plantilla:", error);
      notification.error({ message: "Error al descargar plantilla" });
    }
  };

  const renderMenuPlantillas = () => {
    const items = isDislicoresActive()
      ? [{ key: "Plantilla_Dislicores.xlsx", label: "Plantilla Dislicores" }]
      : [{ key: "Plantilla_Negociacion.xlsx", label: "Plantilla Negociación" }];

    return (
      <Menu onClick={({ key }) => handleDescargarPlantilla(key)}>
        {items.map((it) => (
          <Menu.Item key={it.key}>{it.label}</Menu.Item>
        ))}
      </Menu>
    );
  };

  return (
    <div className="campanas-container">
      <h1 className="excel-tittle">Gestión de Campañas</h1>
      <p className="areas-description">
        Visualizacion de campañas y su envio.
      </p>
      <Space style={{ marginBottom: 16 }}>
        <div className="campanas-toolbar">
        <Button
          type="default"
          icon={<EditOutlined />}
          onClick={() => setSequencesManageModalVisible(true)}
        >
          Administrar Secuencias
        </Button>
        <Button
          type="default"
          icon={<EyeOutlined />}
          onClick={() => setContactListsManageModalVisible(true)}
        >
          Administrar Listas de Contacto
        </Button>
        <Button
          type="default"
          icon={<InfoCircleOutlined />}
          onClick={() => setRedialingRulesManageModalVisible(true)}
        >
          Administrar Reglas Remarcado
        </Button> 

        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setModoCreacionLibre(true);
            setNewDescripcion("");
            setSelectedSequence(null);
            setSelectedContactList(null);
            setSelectedRedialingRule(null);
            setSelectedCountry(null);
            setLulaCreateModalVisible(true);
          }}
        >
          Crear Campaña
        </Button>
        </div>
      </Space>

      <Space
        direction="horizontal"
        style={{
          marginBottom: 16,
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center" }}>
          <span>Filtrar origen:&nbsp;</span>
          <Select
            value={selectedOrigenFilter}
            onChange={setSelectedOrigenFilter}
            style={{ width: 150 }}
          >
            <Select.Option value="todos">Todos</Select.Option>
            <Select.Option value="Aplicativo">Aplicativo</Select.Option>
            <Select.Option value="Gail">Gail</Select.Option>
          </Select>
        </div>

        <div style={{ display: "flex", alignItems: "center" }}>
          <span>Buscar Campañas:&nbsp;</span>
          <Input
            placeholder="Buscar campaña..."
            value={searchTextGlobal}
            onChange={(e) => setSearchTextGlobal(e.target.value)}
            style={{ width: 250 }}
            allowClear
          />
        </div>

        <div style={{ display: "flex", alignItems: "center" }}>
          <span>País:&nbsp;</span>
          <Select
            placeholder="Selecciona el país"
            onChange={(pais) => {
              resetAvailableResources();
              setPaisSeleccionado(pais);
              setApiKeyActiva(API_KEYS_BY_COUNTRY[pais]);
            }}
            style={{ width: 220 }}
          >
            <Select.Option value="Dominicana">
              República Dominicana
            </Select.Option>
            <Select.Option value="SystemGroup Cobro">
              SystemGroup Cobro
            </Select.Option>
            <Select.Option value="SystemGroup">SystemGroup</Select.Option>
            <Select.Option value="Dislicores">Dislicores</Select.Option>
            <Select.Option value="Operacion Peru">Operación Peru</Select.Option>
          </Select>
        </div>
      </Space>

      <Table
        columns={columns}
        dataSource={filteredData}
        rowKey="idCampana"
        pagination={{ pageSize: 5 }}
        bordered
      />

      <Modal
        title={
          selectedCampaignId
            ? "Editar Campaña Backend"
            : "Crear Campaña Backend"
        }
        open={modalVisible}
        onOk={handleSaveBackendCampaign}
        onCancel={handleCancelBackendCampaignModal}
        okText="Guardar"
        cancelText="Cancelar"
      >
        <label>Descripción:</label>
        <Input
          value={newDescripcion}
          onChange={(e) => setNewDescripcion(e.target.value)}
          placeholder="Nombre de la campaña backend"
        />
      </Modal>

      <Modal
        title="Crear Campaña Gail (Lula)"
        open={lulaCreateModalVisible}
        onOk={handleSaveLulaCampaign}
        onCancel={() => {
          setLulaCreateModalVisible(false);
          resetLulaModalState();
          fetchScripts(apiKeyActiva);
        }}
        okText="Crear"
        cancelText="Cancelar"
        confirmLoading={creatingCampaign}
      >
        <Spin spinning={creatingCampaign} tip="Creando campaña...">
          <label>Descripción:</label>
          <Input
            value={newDescripcion}
            onChange={(e) => setNewDescripcion(e.target.value)}
            placeholder="Nombre de la campaña"
            style={{ marginBottom: 8 }}
            disabled={!modoCreacionLibre}
          />

          <label>País:</label>
          <Select
            placeholder="Selecciona el país"
            value={modalCountry}
            onChange={(pais) => {
              setModalCountry(pais);
              setModalApiKey(API_KEYS_BY_COUNTRY[pais]);
            }}
            style={{ width: 300, marginBottom: 20 }}
          >
            <Select.Option value="Dominicana">Dominicana</Select.Option>
            <Select.Option value="SystemGroup">SystemGroup</Select.Option>
            <Select.Option value="SystemGroup Cobro">
              SystemGroup Cobro
            </Select.Option>
            <Select.Option value="Dislicores">Dislicores</Select.Option>
            <Select.Option value="Operacion Peru">Operación Peru</Select.Option>
          </Select>

          <div style={{ marginTop: 20 }}>
            <label>Secuencia:</label>
            <Space>
              <Input
                value={
                  availableSequencesModal.find(
                    (seq) => seq.id === selectedSequence
                  )?.name || "No seleccionada"
                }
                disabled
                style={{ width: "calc(100% - 70px)" }}
              />
              <Button onClick={() => setSequencesManageModalVisible(true)}>
                Elegir
              </Button>
            </Space>
          </div>

          <div style={{ marginTop: 20 }}>
            <label>Lista de Contactos:</label>
            <Space>
              <Select
                value={selectedContactList}
                onChange={setSelectedContactList}
                style={{ width: "calc(100% - 70px)" }}
                placeholder="Selecciona una lista"
                disabled
                suffixIcon={<SearchOutlined />}
              >
                {availableContactListsModal.map((list) => (
                  <Select.Option key={list.id} value={list.id}>
                    {list.name}
                  </Select.Option>
                ))}
              </Select>
              <Button onClick={() => setContactListsManageModalVisible(true)}>
                Elegir
              </Button>
            </Space>
          </div>

          <div style={{ marginTop: 20 }}>
            <label>Reglas de Remarcado:</label>
            <Space>
              <Select
                value={selectedRedialingRule}
                onChange={setSelectedRedialingRule}
                style={{ width: "calc(100% - 70px)" }}
                placeholder="Selecciona una regla"
                disabled
                suffixIcon={<SearchOutlined />}
              >
                {availableRulesModal.map((rule) => (
                  <Select.Option key={rule.id} value={rule.id}>
                    {rule.name}
                  </Select.Option>
                ))}
              </Select>
              <Button onClick={() => setRedialingRulesManageModalVisible(true)}>
                Elegir
              </Button>
            </Space>
          </div>
        </Spin>
      </Modal>

      <Modal
        title="Administrar Secuencias"
        open={sequencesManageModalVisible}
        onCancel={() => setSequencesManageModalVisible(false)}
        footer={null}
        width="80%"
        destroyOnClose
      >
        <Button
          type="primary"
          icon={<PlusOutlined />}
          style={{ marginBottom: 16 }}
          onClick={() => {
            form.resetFields();
            setCreateSequenceModalVisible(true);
          }}
        >
          Crear Nueva Secuencia
        </Button>
        <Input
          placeholder="Buscar secuencia por nombre"
          value={searchSequence}
          onChange={(e) => setSearchSequence(e.target.value)}
          style={{ marginBottom: 16 }}
          prefix={<SearchOutlined />}
          allowClear
        />
        <Table
          columns={sequenceColumns}
          dataSource={filteredSequences}
          rowKey="id"
          size="small"
          scroll={{ y: 400 }}
        />
      </Modal>
      <Modal
        title="Crear Nueva Secuencia "
        open={createSequenceModalVisible}
        onOk={handleCreateNewSequence}
        onCancel={() => {
          setCreateSequenceModalVisible(false);
          form.resetFields();
        }}
        okText="Crear"
        cancelText="Cancelar"
        destroyOnClose
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          name="createSequenceForm"
          initialValues={{ timezone: "America/Bogota" }}
        >
          <Form.Item
            name="name"
            label="Nombre"
            rules={[{ required: true, message: "Ingrese el nombre" }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="description"
            label="Descripción"
            rules={[{ required: true, message: "Ingrese descripción" }]}
          >
            <Input.TextArea rows={2} />
          </Form.Item>

          <Form.Item
            name="timezone"
            label="Zona Horaria"
            rules={[{ required: true, message: "Ingrese zona horaria" }]}
          >
            <Select showSearch placeholder="Seleccione Zona Horaria">
              {timezones.map((tz) => (
                <Select.Option key={tz} value={tz}>
                  {tz}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.List name="schedules">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row
                    gutter={16}
                    key={key}
                    justify="start"
                    style={{
                      marginBottom: 8,
                      border: "1px solid #ddd",
                      padding: 8,
                      borderRadius: 6,
                    }}
                  >
                    <Col span={6}>
                      <Form.Item
                        {...restField}
                        name={[name, "hour"]}
                        label="Hora"
                      >
                        <InputNumber
                          min={0}
                          max={23}
                          style={{ width: "100%" }}
                        />
                      </Form.Item>
                    </Col>

                    <Col span={6}>
                      <Form.Item
                        {...restField}
                        name={[name, "minute"]}
                        label="Minuto"
                      >
                        <InputNumber
                          min={0}
                          max={59}
                          style={{ width: "100%" }}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={6}></Col>

                    <Col span={24}>
                      <Form.Item
                        {...restField}
                        name={[name, "sequenceScripts"]}
                        label="Scripts"
                        rules={[
                          {
                            required: true,
                            message: "Seleccione al menos un script",
                          },
                        ]}
                      >
                        <Select
                          mode="multiple"
                          allowClear
                          placeholder="Seleccione scripts"
                          options={scriptOptions}
                          style={{ width: "100%" }}
                        />
                      </Form.Item>
                    </Col>

                    <Button
                      danger
                      icon={<MinusCircleOutlined />}
                      onClick={() => remove(name)}
                    >
                      Eliminar horario
                    </Button>
                  </Row>
                ))}
                <Button onClick={() => add()} icon={<PlusOutlined />}>
                  Añadir horario
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      <Modal
        title={
          editingSequence ? "Editar Secuencia" : "Crear Secuencia"
        }
        open={editSequenceModalVisible}
        onOk={handleUpdateSequence}
        onCancel={() => {
          setEditSequenceModalVisible(false);
          setEditingSequence(null);
          form.resetFields();
        }}
        okText={editingSequence ? "Actualizar" : "Crear"}
        cancelText="Cancelar"
        destroyOnClose
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          name="sequenceForm"
          initialValues={{ timezone: "America/Bogota" }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Nombre de la Secuencia"
                rules={[
                  {
                    required: true,
                    message: "Por favor ingrese el nombre de la secuencia",
                  },
                ]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="Estado"
                rules={[
                  { required: true, message: "Por favor seleccione el estado" },
                ]}
              >
                <Select placeholder="Seleccione un estado">
                  <Select.Option value="active">Activa</Select.Option>
                  <Select.Option value="inactive">Inactiva</Select.Option>
                  <Select.Option value="archived">Archivada</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="Descripción">
            <Input.TextArea rows={2} />
          </Form.Item>

          <Form.Item
            name="timezone"
            label="Zona Horaria"
            rules={[{ required: true, message: "Seleccione zona horaria" }]}
          >
            <Select
              showSearch
              placeholder="Seleccione zona horaria"
              filterOption={(input, option) =>
                option.value.toLowerCase().includes(input.toLowerCase())
              }
            >
              {timezones.map((tz) => (
                <Select.Option key={tz} value={tz}>
                  {tz}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.List name="schedules" label="Horarios">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Space
                    key={key}
                    style={{ display: "block", marginBottom: 16 /* ... */ }}
                  >
                    <Row gutter={16}>
                      <Col span={6}>
                        <Form.Item
                          {...restField}
                          name={[name, "dayOffset"]}
                          label="Días desde inicio"
                          rules={[
                            {
                              required: true,
                              type: "number",
                              message: "Requerido",
                            },
                          ]}
                        >
                          <InputNumber min={0} style={{ width: "100%" }} />
                        </Form.Item>
                      </Col>
                      <Col span={6}>
                        <Form.Item
                          {...restField}
                          name={[name, "delayInMinutes"]}
                          label="Delay (minutos)"
                          rules={[
                            {
                              required: true,
                              type: "number",
                              message: "Requerido",
                            },
                          ]}
                        >
                          <InputNumber
                            min={-60}
                            max={60}
                            style={{ width: "100%" }}
                          />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          {...restField}
                          name={[name, "time"]}
                          label="Hora exacta"
                          rules={[
                            {
                              required: true,
                              message: "Por favor selecciona la hora",
                            },
                          ]}
                        >
                          <TimePicker
                            format="HH:mm"
                            minuteStep={5}
                            style={{ width: "100%" }}
                          />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item
                      {...restField}
                      name={[name, "sequenceScripts"]}
                      label="Script(s)"
                      rules={[
                        {
                          required: true,
                          message: "Seleccione al menos un Script",
                        },
                      ]}
                    >
                      <Select
                        mode="multiple"
                        placeholder="Seleccione Scripts"
                        options={scriptOptions}
                      />
                    </Form.Item>

                    <Button
                      danger
                      type="link"
                      icon={<MinusCircleOutlined />}
                      onClick={() => remove(name)}
                    >
                      Eliminar Horario
                    </Button>
                  </Space>
                ))}

                <Form.Item>
                  <Button
                    type="dashed"
                    onClick={() => add()}
                    block
                    icon={<PlusOutlined />}
                  >
                    Añadir Horario
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      <Modal
        title="Administrar Listas de Contacto"
        open={contactListsManageModalVisible}
        onCancel={() => setContactListsManageModalVisible(false)}
        footer={null}
        width="80%"
        destroyOnClose
      >
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setCreateContactListModalVisible(true);
              setNewContactListName("");
              setNewContactListDescription("");
            }}
          >
            Crear Nueva Lista
          </Button>
        </Space>
        <Input
          placeholder="Buscar lista de contacto por nombre"
          value={searchContactList}
          onChange={(e) => setSearchContactList(e.target.value)}
          style={{ marginBottom: 16 }}
          prefix={<SearchOutlined />}
          allowClear
        />

        <Table
          columns={contactListColumns}
          dataSource={filteredContactLists}
          rowKey="id"
          size="small"
          scroll={{ y: 400 }}
        />
      </Modal>

      <Modal
        title="Crear Nueva Lista de Contacto"
        open={createContactListModalVisible}
        onOk={handleCreateContactList}
        onCancel={() => setCreateContactListModalVisible(false)}
        okText="Crear"
        cancelText="Cancelar"
        destroyOnClose
      >
        <Form layout="vertical">
          <Form.Item label="Nombre de la Lista" required>
            <Input
              value={newContactListName}
              onChange={(e) => setNewContactListName(e.target.value)}
              placeholder="Ej: Clientes VIP"
            />
          </Form.Item>
          <Form.Item label="Descripción">
            <Input.TextArea
              rows={2}
              value={newContactListDescription}
              onChange={(e) => setNewContactListDescription(e.target.value)}
              placeholder="Descripción de la lista de contactos"
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Contactos en Lista"
        open={contactsInListModalVisible}
        onCancel={() => setContactsInListModalVisible(false)}
        footer={null}
        width="80%"
        destroyOnClose
      >
        <Spin spinning={loadingContacts} tip="Cargando contactos...">
          <Table
            columns={contactsInListTableColumns}
            dataSource={contactsInList}
            rowKey="id"
            size="small"
            scroll={{ y: 400 }}
            locale={{ emptyText: "No hay contactos en esta lista." }}
            pagination={{ pageSize: 10 }}
          />
        </Spin>
      </Modal>

      <Modal
        title={`Añadir Contacto a Lista: ${
          contactLists.find(
            (list) => list.id === selectedContactListForAddingContact
          )?.name || ""
        }`}
        open={addContactModalVisible}
        onOk={handleSaveContact}
        onCancel={() => setAddContactModalVisible(false)}
        okText="Añadir"
        cancelText="Cancelar"
        destroyOnClose
        width={700}
      >
        <Spin spinning={loadingExcel} tip="Procesando Excel...">
          <Dropdown overlay={renderMenuPlantillas} placement="bottomLeft">
            <Button icon={<DownloadOutlined />}>Descargar Plantilla</Button>
          </Dropdown>
          <Upload />
          <Upload
            beforeUpload={async (file) => {
              if (!selectedContactListForAddingContact) {
                notification.warning({
                  message: "Selecciona primero una lista de contactos.",
                });
                return false;
              }
              try {
                const key = (modalApiKey || apiKeyActiva || "").trim();
                const parser =
                  key === LULA_API_KEY_DISLICORES
                    ? handleExcelUploadDislicores
                    : handleExcelUpload;

                const contacts = await parser(file);

                await handleBulkAddContactsToList(
                  selectedContactListForAddingContact,
                  contacts
                );
              } catch (_) {}
              return false;
            }}
            accept=".xlsx, .xls"
            showUploadList={false}
          >
            <Button
              type="primary"
              icon={<UploadOutlined />}
              disabled={!selectedContactListForAddingContact}
            >
              Cargar y Crear Contactos
            </Button>
          </Upload>

          <Form form={addContactForm} layout="vertical" name="addContactForm">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="firstName"
                  label="Primer Nombre"
                  rules={[
                    {
                      required: true,
                      message: "Por favor ingrese el primer nombre",
                    },
                  ]}
                >
                  <Input />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="lastName" label="Apellido">
                  <Input />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="businessName" label="Nombre de Negocio">
              <Input />
            </Form.Item>

            <Form.List name="phoneNumbers" label="Números de Teléfono">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space
                      key={key}
                      style={{ display: "flex", marginBottom: 8 }}
                      align="baseline"
                    >
                      <Form.Item
                        {...restField}
                        name={[name, "number"]}
                        rules={[
                          {
                            required: true,
                            message: "Número de teléfono requerido",
                          },
                        ]}
                        style={{ flex: 1, marginRight: 8 }}
                      >
                        <Input placeholder="Número" />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, "type"]}
                        rules={[{ required: true, message: "Tipo requerido" }]}
                        initialValue="mobile"
                        style={{ width: 120 }}
                      >
                        <Select placeholder="Tipo">
                          <Select.Option value="mobile">Móvil</Select.Option>
                          <Select.Option value="home">Casa</Select.Option>
                          <Select.Option value="work">Trabajo</Select.Option>
                        </Select>
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} />
                    </Space>
                  ))}
                  <Form.Item>
                    <Button
                      type="dashed"
                      onClick={() => add({ number: "", type: "mobile" })}
                      block
                      icon={<PlusOutlined />}
                    >
                      Añadir Teléfono
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>

            <Form.List name="emails" label="Correos Electrónicos">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space
                      key={key}
                      style={{ display: "flex", marginBottom: 8 }}
                      align="baseline"
                    >
                      <Form.Item
                        {...restField}
                        name={[name, "email"]}
                        style={{ flex: 1, marginRight: 8 }}
                      >
                        <Input placeholder="Correo" />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, "type"]}
                        initialValue="work"
                        style={{ width: 120 }}
                      >
                        <Select placeholder="Tipo">
                          <Select.Option value="work">Trabajo</Select.Option>
                          <Select.Option value="home">Casa</Select.Option>
                        </Select>
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} />
                    </Space>
                  ))}
                  <Form.Item>
                    <Button
                      type="dashed"
                      onClick={() => add({ email: "", type: "work" })}
                      block
                      icon={<PlusOutlined />}
                    >
                      Añadir Correo
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>

            <Form.List
              name="additionalData"
              label="Datos Adicionales"
              initialValue={defaultAdditionalDataFields}
            >
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space
                      key={key}
                      style={{ display: "flex", marginBottom: 8 }}
                      align="baseline"
                    >
                      <Form.Item
                        {...restField}
                        name={[name, "key"]}
                        rules={[{ required: true, message: "Clave requerida" }]}
                        style={{ width: 150, marginRight: 8 }}
                      >
                        <Input placeholder="Clave (ej: banco)" />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, "value"]}
                        style={{ flex: 1, marginRight: 8 }}
                      >
                        <Input placeholder="Valor (ej: Tuya)" />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} />
                    </Space>
                  ))}
                  <Form.Item>
                    <Button
                      type="dashed"
                      onClick={() => add({ key: "", value: "" })}
                      block
                      icon={<PlusOutlined />}
                    >
                      Añadir Dato Adicional Personalizado
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="source" label="Fuente">
                  <Input placeholder="Ej: Manual" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="status" label="Estado" initialValue="active">
                  <Select>
                    <Select.Option value="active">Activo</Select.Option>
                    <Select.Option value="inactive">Inactivo</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Spin>
      </Modal>

      <Modal
        title="Detalles de Datos Adicionales"
        open={additionalDataModalVisible}
        onCancel={() => setAdditionalDataModalVisible(false)}
        footer={null}
        destroyOnClose
        width={600}
      >
        {currentAdditionalData &&
        Object.keys(currentAdditionalData).length > 0 ? (
          <Descriptions bordered column={1} size="small">
            {Object.entries(currentAdditionalData).map(([key, value]) => {
              if (value === null || value === "" || value === undefined)
                return null;

              let displayValue = value;
              if (
                [
                  "Capital",
                  "Oferta 1",
                  "Oferta 2",
                  "Oferta 3",
                  "Intereses",
                  "Saldo total",
                  "Hasta 3 cuotas",
                  "Hasta 6 cuotas",
                ].includes(key)
              ) {
                displayValue = formatCurrency(value);
              }

              return (
                <Descriptions.Item key={key} label={key}>
                  {displayValue}
                </Descriptions.Item>
              );
            })}
          </Descriptions>
        ) : (
          <p>No hay datos adicionales disponibles para este contacto.</p>
        )}
      </Modal>

      <Modal
        title="Administrar Reglas de Remarcado"
        open={redialingRulesManageModalVisible}
        onCancel={() => setRedialingRulesManageModalVisible(false)}
        footer={null}
        width="80%"
        destroyOnClose
      >
        <Input
          placeholder="Buscar regla por nombre"
          value={searchRedialingRule}
          onChange={(e) => setSearchRedialingRule(e.target.value)}
          style={{ marginBottom: 16 }}
          prefix={<SearchOutlined />}
          allowClear
        />
        <Table
          columns={redialingRulesColumns}
          dataSource={filteredRedialingRules}
          rowKey="id"
          size="small"
          scroll={{ y: 400 }}
        />
      </Modal>

      <Modal
        title="Detalles de Regla de Remarcado"
        open={redialingRuleDetailModalVisible}
        onCancel={() => setRedialingRuleDetailModalVisible(false)}
        footer={null}
        destroyOnClose
        width={800}
      >
        <Spin
          spinning={loadingRedialingRuleDetails}
          tip="Cargando detalles de la regla..."
        >
          {currentRedialingRuleDetails ? (
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="ID">
                {currentRedialingRuleDetails.id}
              </Descriptions.Item>
              <Descriptions.Item label="Nombre">
                {currentRedialingRuleDetails.name}
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                {currentRedialingRuleDetails.status}
              </Descriptions.Item>
              <Descriptions.Item label="Máx Intentos">
                {currentRedialingRuleDetails.outreachMaxAttempts}
              </Descriptions.Item>
              <Descriptions.Item label="Máx Intentos por Número">
                {currentRedialingRuleDetails.outreachMaxAttemptsForNumber}
              </Descriptions.Item>

              <Descriptions.Item label="Outcomes">
                {currentRedialingRuleDetails.outcomes &&
                currentRedialingRuleDetails.outcomes.length > 0
                  ? currentRedialingRuleDetails.outcomes.map(
                      (outcome, index) => (
                        <div key={index} style={{ marginBottom: "8px" }}>
                          <Tag color="blue">{outcome.name}</Tag>:{" "}
                          {outcome.definition}
                        </div>
                      )
                    )
                  : "N/A"}
              </Descriptions.Item>

              <Descriptions.Item label="Acciones del Sistema">
                {currentRedialingRuleDetails.systemActions &&
                Object.keys(currentRedialingRuleDetails.systemActions).length >
                  0
                  ? Object.entries(
                      currentRedialingRuleDetails.systemActions
                    ).map(([key, actions], idx) => (
                      <div key={idx} style={{ marginBottom: "8px" }}>
                        <strong>{key}:</strong>
                        {actions && actions.length > 0
                          ? actions.map((actionItem, actionIdx) => (
                              <ul
                                key={actionIdx}
                                style={{
                                  listStyleType: "none",
                                  paddingLeft: "20px",
                                }}
                              >
                                <li>- Demora: {actionItem.delay}</li>
                                <li>
                                  - Máx Intentos: {actionItem.maxAttempts}
                                </li>
                                <li>- Acción: {actionItem.action}</li>
                              </ul>
                            ))
                          : "N/A"}
                      </div>
                    ))
                  : "N/A"}
              </Descriptions.Item>
            </Descriptions>
          ) : (
            <p>No se encontraron detalles para esta regla.</p>
          )}
        </Spin>
      </Modal>

      <Modal
        title={`Resultados de Campaña: ${currentCampaignForTouchpoints || ""}`}
        open={touchpointsModalVisible}
        onCancel={() => setTouchpointsModalVisible(false)}
        footer={null}
        destroyOnClose
        width="95%"
      >
        <Spin
          spinning={touchpointsLoading}
          tip="Cargando resultados de la campaña..."
        >
          {campaignTouchpoints.length > 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "row",
                alignItems: "flex-start",
                gap: 32,
              }}
            >
              <div style={{ width: 400, height: 400 }}>
                <Pie
                  data={processTouchpointsForChart(campaignTouchpoints)}
                  options={{
                    maintainAspectRatio: false,
                    plugins: {
                      tooltip: {
                        callbacks: {
                          label: (tooltipItem) => {
                            const dataset = tooltipItem.dataset;
                            const total = dataset.data.reduce(
                              (sum, val) => sum + val,
                              0
                            );
                            const value = dataset.data[tooltipItem.dataIndex];
                            const percentage = ((value / total) * 100).toFixed(
                              1
                            );
                            const label =
                              dataset.labels?.[tooltipItem.dataIndex] ||
                              "Cantidad";
                            return `${label}: ${value} (${percentage}%)`;
                          },
                        },
                      },
                    },
                    onClick: (evt, elements) => {
                      if (elements && elements.length > 0) {
                        const chart = elements[0];
                        const label = chart.element.$context.raw.label;
                        setSelectedOutcomeFilter(label);
                      }
                    },
                  }}
                />
              </div>

              <div style={{ flex: 0.8, marginTop: "-40px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <h2>Detalle de Llamadas {selectedOutcomeFilter}</h2>
                  <Space>
                    {selectedOutcomeFilter && (
                      <Button
                        onClick={() => setSelectedOutcomeFilter(null)}
                        size="small"
                        type="link"
                      >
                        Limpiar Filtro
                      </Button>
                    )}
                    <Button
                      icon={<DownloadOutlined />}
                      size="small"
                      type="primary"
                      onClick={() =>
                        handleDownloadTouchpointsExcel(
                          selectedOutcomeFilter
                            ? campaignTouchpoints.filter(
                                (tp) => tp.outcome === selectedOutcomeFilter
                              )
                            : campaignTouchpoints,
                          currentCampaignForTouchpoints
                        )
                      }
                    >
                      Descargar Excel
                    </Button>
                  </Space>
                </div>

                <Input.Search
                  placeholder="Buscar por nombre o Resultado"
                  allowClear
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ marginBottom: 16, width: 250 }}
                />

                <Table
                  dataSource={(selectedOutcomeFilter
                    ? campaignTouchpoints.filter(
                        (tp) => tp.outcome === selectedOutcomeFilter
                      )
                    : campaignTouchpoints
                  ).filter((tp) => {
                    const search = searchText.toLowerCase();
                    return (
                      tp.contactFirstName?.toLowerCase().includes(search) ||
                      tp.outcome?.toLowerCase().includes(search)
                    );
                  })}
                  rowKey="contactId"
                  pagination={{ pageSize: 5 }}
                  expandable={{
                    expandedRowRender: (record) => (
                      <Table
                        dataSource={(record.transcript || []).map(
                          (line, idx) => ({
                            key: idx,
                            role:
                              line.role === "assistant"
                                ? "Asistente"
                                : "Usuario",
                            content: line.content,
                          })
                        )}
                        columns={[
                          { title: "Quién", dataIndex: "role", key: "role" },
                          {
                            title: "Mensaje",
                            dataIndex: "content",
                            key: "content",
                          },
                        ]}
                        pagination={false}
                        size="small"
                        rowKey="key"
                      />
                    ),
                    rowExpandable: (record) =>
                      record.transcript && record.transcript.length > 0,
                  }}
                  columns={[
                    {
                      title: "Nombre",
                      dataIndex: "contactFirstName",
                      key: "contactFirstName",
                      sorter: (a, b) =>
                        (a.contactFirstName || "").localeCompare(
                          b.contactFirstName || ""
                        ),
                    },
                    {
                      title: "Resultado",
                      dataIndex: "outcome",
                      key: "outcome",
                      sorter: (a, b) =>
                        (a.outcome || "").localeCompare(b.outcome || ""),
                      render: (value) => {
                        const colorMap = {
                          "too-short": "volcano",
                          voicemail: "geekblue",
                          "no-answer": "orange",
                          failed: "red",
                          other: "purple",
                          EQUIVOCADO: "gold",
                        };
                        return (
                          <Tag color={colorMap[value] || "default"}>
                            {value?.toUpperCase()}
                          </Tag>
                        );
                      },
                    },
                    {
                      title: "Teléfono",
                      dataIndex: "phoneNumber",
                      key: "phoneNumber",
                      sorter: (a, b) =>
                        (a.phoneNumber || "").localeCompare(
                          b.phoneNumber || ""
                        ),
                    },
                  ]}
                />
              </div>
            </div>
          ) : (
            <p style={{ textAlign: "center" }}>
              No se encontraron resultados para esta campaña.
            </p>
          )}
        </Spin>
      </Modal>
    </div>
  );
};

export default CampanasGail;