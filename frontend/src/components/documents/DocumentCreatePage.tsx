import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useCanvasNavigate } from '@/hooks/useCanvasNavigate';
import {
  ArrowLeft,
  Loader2,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  MessageSquare,
  FileWarning,
  Siren,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { useCreateDocument, useGenerateDocument } from '@/hooks/useDocuments';
import { ROUTES, DOCUMENT_TYPES, type DocumentTypeConfig } from '@/lib/constants';
import { cn } from '@/lib/utils';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  ShieldCheck,
  AlertTriangle,
  MessageSquare,
  FileWarning,
  Siren,
};

const STEPS = [
  { id: 1, label: 'Select Type' },
  { id: 2, label: 'Fill Details' },
  { id: 3, label: 'Generate' },
  { id: 4, label: 'Review' },
];

const GENERATION_MESSAGES = [
  'Analyzing document requirements...',
  'Reviewing safety regulations...',
  'Generating document structure...',
  'Writing content sections...',
  'Applying compliance standards...',
  'Formatting final document...',
  'Almost done...',
];

export function DocumentCreatePage() {
  const navigate = useCanvasNavigate();
  const [searchParams] = useSearchParams();
  const preselectedType = searchParams.get('type');

  const [step, setStep] = useState(preselectedType ? 2 : 1);
  const [selectedType, setSelectedType] = useState<DocumentTypeConfig | null>(
    preselectedType ? DOCUMENT_TYPES.find((t) => t.id === preselectedType) || null : null
  );
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [generationMessage, setGenerationMessage] = useState(0);
  const [pendingType, setPendingType] = useState<DocumentTypeConfig | null>(null);
  const [showTypeChangeDialog, setShowTypeChangeDialog] = useState(false);

  const createDocument = useCreateDocument();
  const generateDocument = useGenerateDocument();

  const isGenerating = createDocument.isPending || generateDocument.isPending;

  useEffect(() => {
    if (!isGenerating) return;

    const interval = setInterval(() => {
      setGenerationMessage((prev) =>
        prev < GENERATION_MESSAGES.length - 1 ? prev + 1 : prev
      );
    }, 2500);

    return () => clearInterval(interval);
  }, [isGenerating]);

  const hasFilledFields = Object.values(fieldValues).some((v) => v.trim());

  const handleSelectType = (type: DocumentTypeConfig) => {
    if (selectedType && selectedType.id !== type.id && hasFilledFields) {
      setPendingType(type);
      setShowTypeChangeDialog(true);
      return;
    }
    setSelectedType(type);
    setFieldValues({});
    setStep(2);
  };

  const confirmTypeChange = () => {
    if (pendingType) {
      setSelectedType(pendingType);
      setFieldValues({});
      setStep(2);
    }
    setPendingType(null);
    setShowTypeChangeDialog(false);
  };

  const cancelTypeChange = () => {
    setPendingType(null);
    setShowTypeChangeDialog(false);
  };

  const handleFieldChange = (fieldId: string, value: string) => {
    setFieldValues((prev) => ({ ...prev, [fieldId]: value }));
  };

  const isFormValid = () => {
    if (!selectedType) return false;
    return selectedType.fields
      .filter((f) => f.required)
      .every((f) => fieldValues[f.id]?.trim());
  };

  const handleGenerate = async () => {
    if (!selectedType || !isFormValid()) return;

    setStep(3);
    setGenerationMessage(0);

    try {
      const title =
        fieldValues['project_name'] ||
        fieldValues['job_title'] ||
        fieldValues['topic'] ||
        fieldValues['site_name'] ||
        `${selectedType.name} - ${new Date().toLocaleDateString()}`;

      const doc = await createDocument.mutateAsync({
        title,
        document_type: selectedType.id,
        project_info: fieldValues,
      });

      await generateDocument.mutateAsync({ document_id: doc.id });
      navigate(ROUTES.DOCUMENT_EDIT(doc.id));
    } catch {
      setStep(2);
    }
  };

  const renderStepIndicator = () => (
    <div className="mb-8 flex items-center justify-center">
      {STEPS.map((s, index) => (
        <div key={s.id} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors',
                step > s.id
                  ? 'bg-primary text-primary-foreground'
                  : step === s.id
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
              )}
            >
              {step > s.id ? <Check className="h-4 w-4" /> : s.id}
            </div>
            <span
              className={cn(
                'mt-1 text-xs',
                step >= s.id ? 'text-[var(--concrete-600)]' : 'text-muted-foreground'
              )}
            >
              {s.label}
            </span>
          </div>
          {index < STEPS.length - 1 && (
            <div
              className={cn(
                'mx-2 mb-5 h-0.5 w-12 sm:w-16',
                step > s.id ? 'bg-primary' : 'bg-muted'
              )}
            />
          )}
        </div>
      ))}
    </div>
  );

  const renderTypeSelection = () => (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 text-center">
        <h2 className="text-xl font-semibold text-foreground">Choose Document Type</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Select the type of safety document you want to generate
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {DOCUMENT_TYPES.map((type) => {
          const IconComponent = ICON_MAP[type.icon] || ShieldCheck;
          return (
            <Card
              key={type.id}
              className={cn(
                'cursor-pointer transition-all hover:shadow-md',
                selectedType?.id === type.id && 'ring-2 ring-primary'
              )}
              onClick={() => handleSelectType(type)}
            >
              <CardContent className="pt-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--machine-wash)]">
                  <IconComponent className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mt-3 font-semibold text-foreground">{type.name}</h3>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {type.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );

  const renderFieldForm = () => {
    if (!selectedType) return null;

    return (
      <div className="mx-auto max-w-2xl">
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setStep(1)}
            className="mb-2"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            Change type
          </Button>
          <h2 className="text-xl font-semibold text-foreground">{selectedType.name}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Fill in the details below to generate your document
          </p>
        </div>

        <Card>
          <CardContent className="space-y-5 pt-6">
            {selectedType.fields.map((field) => (
              <div key={field.id} className="space-y-2">
                <Label htmlFor={field.id}>
                  {field.label}
                  {field.required && <span className="ml-1 text-[var(--fail)]">*</span>}
                </Label>

                {field.type === 'text' && (
                  <Input
                    id={field.id}
                    placeholder={field.placeholder}
                    value={fieldValues[field.id] || ''}
                    onChange={(e) => handleFieldChange(field.id, e.target.value)}
                  />
                )}

                {field.type === 'textarea' && (
                  <Textarea
                    id={field.id}
                    placeholder={field.placeholder}
                    value={fieldValues[field.id] || ''}
                    onChange={(e) => handleFieldChange(field.id, e.target.value)}
                    rows={3}
                  />
                )}

                {field.type === 'select' && field.options && (
                  <Select
                    value={fieldValues[field.id] || ''}
                    onValueChange={(v) => handleFieldChange(field.id, v ?? '')}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                {field.type === 'date' && (
                  <Input
                    id={field.id}
                    type="date"
                    value={fieldValues[field.id] || ''}
                    onChange={(e) => handleFieldChange(field.id, e.target.value)}
                  />
                )}

                {field.type === 'number' && (
                  <Input
                    id={field.id}
                    type="number"
                    placeholder={field.placeholder}
                    value={fieldValues[field.id] || ''}
                    onChange={(e) => handleFieldChange(field.id, e.target.value)}
                  />
                )}
              </div>
            ))}

            <Separator />

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => navigate(ROUTES.DOCUMENTS)}>
                Cancel
              </Button>
              <Button
                className="bg-primary hover:bg-[var(--machine-dark)]"
                disabled={!isFormValid()}
                onClick={handleGenerate}
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Document
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderGenerating = () => (
    <div className="flex flex-col items-center py-16 text-center">
      <div className="relative">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--machine-wash)]">
          <Sparkles className="h-10 w-10 text-primary" />
        </div>
        <div className="absolute -bottom-1 -right-1">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      </div>

      <h2 className="mt-6 text-xl font-semibold text-foreground">
        Generating Your Document
      </h2>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        Our AI is creating a comprehensive, regulation-compliant safety document based on your inputs.
      </p>

      <div className="mt-8 flex flex-col items-center gap-2">
        {GENERATION_MESSAGES.map((msg, index) => (
          <div
            key={index}
            className={cn(
              'flex items-center gap-2 text-sm transition-all duration-300',
              index < generationMessage
                ? 'text-[var(--pass)]'
                : index === generationMessage
                  ? 'text-[var(--machine-dark)] font-medium'
                  : 'text-muted-foreground'
            )}
          >
            {index < generationMessage ? (
              <Check className="h-4 w-4" />
            ) : index === generationMessage ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <div className="h-4 w-4" />
            )}
            {msg}
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-4 flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.DOCUMENTS)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Create Document</h1>
          <p className="text-sm text-muted-foreground">Generate a new safety compliance document</p>
        </div>
      </div>

      {renderStepIndicator()}

      {step === 1 && renderTypeSelection()}
      {step === 2 && renderFieldForm()}
      {step === 3 && renderGenerating()}

      {/* Confirmation dialog when changing type after filling fields */}
      <Dialog open={showTypeChangeDialog} onOpenChange={setShowTypeChangeDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Change Document Type?</DialogTitle>
            <DialogDescription>
              You have already filled in some fields. Changing the document type will clear all entered data. Do you want to continue?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelTypeChange}>
              Cancel
            </Button>
            <Button
              className="bg-primary hover:bg-[var(--machine-dark)]"
              onClick={confirmTypeChange}
            >
              Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
