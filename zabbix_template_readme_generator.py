import yaml
import os
import argparse

def sanitize_description(text):
    return text.replace('\n', '<br>').replace('|', '\\|')

def dual_description(text, do_translate=False):
    if not do_translate or not text.strip():
        return text
    try:
        from deep_translator import GoogleTranslator
        ru = GoogleTranslator(source='auto', target='ru').translate(text)
        # Перевод, затем оригинал курсивом через <br>
        return f"{ru}<br><i>{text}</i>"
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def markdown_table(headers, rows):
    table = '| ' + ' | '.join(headers) + ' |\n'
    table += '| ' + ' | '.join(['---']*len(headers)) + ' |\n'
    for row in rows:
        row = [sanitize_description(str(cell)) for cell in row]
        table += '| ' + ' | '.join(row) + ' |\n'
    return table

def load_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def extract_items(template, do_translate):
    items = []
    for item in template.get('items', []):
        items.append({
            'name': item.get('name', ''),
            'key': item.get('key', ''),
            'type': item.get('type', ''),
            'value_type': item.get('value_type', ''),
            'units': item.get('units', ''),
            'description': dual_description(item.get('description', ''), do_translate)
        })
    return items

def extract_macros(template, do_translate):
    macros = []
    for m in template.get('macros', []):
        macros.append({
            'macro': m.get('macro', ''),
            'value': m.get('value', ''),
            'description': dual_description(m.get('description', ''), do_translate)
        })
    return macros

def extract_triggers(template, do_translate):
    triggers = []
    for item in template.get('items', []):
        for trigger in item.get('triggers', []):
            triggers.append({
                'name': trigger.get('name', ''),
                'expression': trigger.get('expression', ''),
                'priority': trigger.get('priority', ''),
                'description': dual_description(trigger.get('description', ''), do_translate)
            })
    for trig in template.get('triggers', []):
        triggers.append({
            'name': trig.get('name', ''),
            'expression': trig.get('expression', ''),
            'priority': trig.get('priority', ''),
            'description': dual_description(trig.get('description', ''), do_translate)
        })
    return triggers

def extract_discovery_rules(template, do_translate):
    drules = []
    for d in template.get('discovery_rules', []):
        drules.append({
            'name': d.get('name', ''),
            'key': d.get('key', ''),
            'description': dual_description(d.get('description', ''), do_translate)
        })
    return drules

def main():
    parser = argparse.ArgumentParser(
        description="Генерация документации по шаблону Zabbix с опциональным автопереводом описаний (перевод + оригинал)."
    )
    parser.add_argument('input', help='YAML-файл шаблона Zabbix (экспорт из Zabbix)')
    parser.add_argument('output', nargs='?', default='README_template.md', help='Имя выходного MD-файла (по умолчанию README_template.md)')
    parser.add_argument('--translate', action='store_true', help='Добавить перевод описаний на русский (вместе с оригиналом)')
    args = parser.parse_args()

    template_path = args.input
    output_md = args.output
    do_translate = args.translate

    if not os.path.exists(template_path):
        print(f"Файл {template_path} не найден.")
        exit(1)

    data = load_template(template_path)
    templates = data.get('zabbix_export', {}).get('templates', [])
    md_output = ""
    for tpl in templates:
        md_output += f"# Template: {tpl.get('template', '')}\n\n"
        description = tpl.get('description', '').strip()
        if description:
            md_output += f"{sanitize_description(dual_description(description, do_translate))}\n\n"

        items = extract_items(tpl, do_translate)
        if items:
            md_output += "## Items\n\n"
            headers = ["Name", "Key", "Type", "Value type", "Units", "Description"]
            rows = [[i['name'], i['key'], str(i['type']), str(i['value_type']), i['units'], i['description']] for i in items]
            md_output += markdown_table(headers, rows) + "\n\n"

        triggers = extract_triggers(tpl, do_translate)
        if triggers:
            md_output += "## Triggers\n\n"
            headers = ["Name", "Expression", "Priority", "Description"]
            rows = [[t['name'], t['expression'], t['priority'], t['description']] for t in triggers]
            md_output += markdown_table(headers, rows) + "\n\n"

        macros = extract_macros(tpl, do_translate)
        if macros:
            md_output += "## Macros\n\n"
            headers = ["Macro", "Value", "Description"]
            rows = [[m.get('macro', ''), m.get('value', ''), m.get('description', '')] for m in macros]
            md_output += markdown_table(headers, rows) + "\n\n"

        discovery_rules = extract_discovery_rules(tpl, do_translate)
        if discovery_rules:
            md_output += "## Discovery rules\n\n"
            headers = ["Name", "Key", "Description"]
            rows = [[d.get('name', ''), d.get('key', ''), d.get('description', '')] for d in discovery_rules]
            md_output += markdown_table(headers, rows) + "\n\n"
            for dr in tpl.get('discovery_rules', []):
                item_protos = dr.get('item_prototypes', [])
                if item_protos:
                    md_output += f"### Item prototypes for discovery: {dr.get('name')}\n\n"
                    headers = ["Name", "Key", "Type", "Value type", "Units", "Description"]
                    rows = [
                        [
                            ip.get('name', ''),
                            ip.get('key', ''),
                            str(ip.get('type', '')),
                            str(ip.get('value_type', '')),
                            ip.get('units', ''),
                            dual_description(ip.get('description', ''), do_translate)
                        ]
                        for ip in item_protos
                    ]
                    md_output += markdown_table(headers, rows) + "\n\n"
                trigger_protos = dr.get('trigger_prototypes', [])
                if trigger_protos:
                    md_output += f"### Trigger prototypes for discovery: {dr.get('name')}\n\n"
                    headers = ["Name", "Expression", "Priority", "Description"]
                    rows = [[tp.get('name', ''), tp.get('expression', ''), tp.get('priority', ''), dual_description(tp.get('description', ''), do_translate)] for tp in trigger_protos]
                    md_output += markdown_table(headers, rows) + "\n\n"
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(md_output)
    print(f"Документация сохранена в {output_md}")

if __name__ == "__main__":
    main()
    