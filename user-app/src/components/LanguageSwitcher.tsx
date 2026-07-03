import { Select } from "@movu/ui";
import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";

const languages = [
  { code: "en", label: "EN" },
  { code: "zh", label: "中文" },
  { code: "ms", label: "BM" }
];

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  return (
    <label className="language-switcher">
      <Languages size={16} aria-hidden="true" />
      <span className="sr-only">{t("common.language")}</span>
      <Select value={i18n.language} onChange={(event) => i18n.changeLanguage(event.target.value)}>
        {languages.map((language) => (
          <option key={language.code} value={language.code}>
            {language.label}
          </option>
        ))}
      </Select>
    </label>
  );
}
