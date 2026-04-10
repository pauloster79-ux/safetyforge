import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import React from 'react';

export type Locale = 'en' | 'es';

const translations: Record<Locale, Record<string, string>> = {
  en: {
    'common.pass': 'Pass',
    'common.fail': 'Fail',
    'common.na': 'N/A',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.back': 'Back',
    'common.submit': 'Submit',
    'common.loading': 'Loading...',
    'common.completed': 'Completed',
    'common.scheduled': 'Scheduled',
    'common.in_progress': 'In Progress',
    'common.all': 'All',
    'common.none': 'None',
    'common.yes': 'Yes',
    'common.no': 'No',
    'common.close': 'Close',
    'common.add': 'Add',
    'common.remove': 'Remove',
    'common.edit': 'Edit',
    'common.view': 'View',
    'common.print': 'Print',
    'common.export': 'Export',
    'toolbox.sign_attendance': 'Sign Attendance',
    'toolbox.complete_talk': 'Complete Talk',
    'toolbox.discussion_questions': 'Discussion Questions',
    'toolbox.key_points': 'Key Points',
    'toolbox.safety_reminders': 'Safety Reminders',
    'toolbox.topic_overview': 'Topic Overview',
    'toolbox.workers_signed': '{count} of {total} workers signed',
    'toolbox.osha_reference': 'OSHA Reference',
    'toolbox.real_world_example': 'Real-World Example',
    'toolbox.attendance': 'Attendance',
    'toolbox.record_attendance': 'Record Attendance',
    'toolbox.worker_name': 'Worker Name',
    'toolbox.sign': 'Sign',
    'toolbox.presented_by': 'Presented by',
    'toolbox.completed_at': 'Completed at',
    'toolbox.new_toolbox_talk': 'New Toolbox Talk',
    'toolbox.generate_talk': 'Generate Talk',
    'toolbox.topic': 'Topic',
    'toolbox.target_audience': 'Target Audience',
    'toolbox.duration': 'Duration',
    'toolbox.language': 'Language',
    'toolbox.custom_points': 'Custom Points',
    'toolbox.custom_points_placeholder': 'Any specific points you want covered?',
    'toolbox.all_workers': 'All Workers',
    'toolbox.new_hires': 'New Hires',
    'toolbox.supervisors': 'Supervisors',
    'toolbox.specific_trade': 'Specific Trade',
    'toolbox.english': 'English',
    'toolbox.spanish': 'Spanish',
    'toolbox.both': 'Both',
    'toolbox.minutes': 'min',
    'toolbox.osha_references': 'OSHA References',
    'toolbox.no_talks': 'No toolbox talks yet',
    'toolbox.no_talks_desc': 'Schedule your first toolbox talk to keep your crew safe',
    'toolbox.recent_talks': 'Recent Toolbox Talks',
    'toolbox.attendees': 'attendees',
    'inspection.checklist': 'Inspection Checklist',
    'inspection.items_completed': '{count} of {total} items completed',
  },
  es: {
    'common.pass': 'Aprobado',
    'common.fail': 'Fallo',
    'common.na': 'N/A',
    'common.save': 'Guardar',
    'common.cancel': 'Cancelar',
    'common.delete': 'Eliminar',
    'common.back': 'Volver',
    'common.submit': 'Enviar',
    'common.loading': 'Cargando...',
    'common.completed': 'Completado',
    'common.scheduled': 'Programado',
    'common.in_progress': 'En Progreso',
    'common.all': 'Todos',
    'common.none': 'Ninguno',
    'common.yes': 'Si',
    'common.no': 'No',
    'common.close': 'Cerrar',
    'common.add': 'Agregar',
    'common.remove': 'Quitar',
    'common.edit': 'Editar',
    'common.view': 'Ver',
    'common.print': 'Imprimir',
    'common.export': 'Exportar',
    'toolbox.sign_attendance': 'Firmar Asistencia',
    'toolbox.complete_talk': 'Completar Charla',
    'toolbox.discussion_questions': 'Preguntas de Discusion',
    'toolbox.key_points': 'Puntos Clave',
    'toolbox.safety_reminders': 'Recordatorios de Seguridad',
    'toolbox.topic_overview': 'Resumen del Tema',
    'toolbox.workers_signed': '{count} de {total} trabajadores firmaron',
    'toolbox.osha_reference': 'Referencia OSHA',
    'toolbox.real_world_example': 'Ejemplo del Mundo Real',
    'toolbox.attendance': 'Asistencia',
    'toolbox.record_attendance': 'Registrar Asistencia',
    'toolbox.worker_name': 'Nombre del Trabajador',
    'toolbox.sign': 'Firmar',
    'toolbox.presented_by': 'Presentado por',
    'toolbox.completed_at': 'Completado a las',
    'toolbox.new_toolbox_talk': 'Nueva Charla de Seguridad',
    'toolbox.generate_talk': 'Generar Charla',
    'toolbox.topic': 'Tema',
    'toolbox.target_audience': 'Audiencia Objetivo',
    'toolbox.duration': 'Duracion',
    'toolbox.language': 'Idioma',
    'toolbox.custom_points': 'Puntos Personalizados',
    'toolbox.custom_points_placeholder': 'Algun punto especifico que desee cubrir?',
    'toolbox.all_workers': 'Todos los Trabajadores',
    'toolbox.new_hires': 'Nuevos Empleados',
    'toolbox.supervisors': 'Supervisores',
    'toolbox.specific_trade': 'Oficio Especifico',
    'toolbox.english': 'Ingles',
    'toolbox.spanish': 'Espanol',
    'toolbox.both': 'Ambos',
    'toolbox.minutes': 'min',
    'toolbox.osha_references': 'Referencias OSHA',
    'toolbox.no_talks': 'No hay charlas de seguridad',
    'toolbox.no_talks_desc': 'Programe su primera charla para mantener seguro a su equipo',
    'toolbox.recent_talks': 'Charlas de Seguridad Recientes',
    'toolbox.attendees': 'asistentes',
    'inspection.checklist': 'Lista de Inspeccion',
    'inspection.items_completed': '{count} de {total} elementos completados',
  },
};

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function getDefaultLocale(): Locale {
  const stored = localStorage.getItem('kerf_locale');
  if (stored === 'en' || stored === 'es') return stored;
  if (typeof navigator !== 'undefined' && navigator.language.startsWith('es')) return 'es';
  return 'en';
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getDefaultLocale);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem('kerf_locale', newLocale);
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      let value = translations[locale][key] || translations['en'][key] || key;
      if (params) {
        for (const [paramKey, paramValue] of Object.entries(params)) {
          value = value.replace(`{${paramKey}}`, String(paramValue));
        }
      }
      return value;
    },
    [locale]
  );

  useEffect(() => {
    localStorage.setItem('kerf_locale', locale);
  }, [locale]);

  return React.createElement(
    LocaleContext.Provider,
    { value: { locale, setLocale, t } },
    children
  );
}

export function useLocale(): LocaleContextValue {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within a LocaleProvider');
  }
  return context;
}
