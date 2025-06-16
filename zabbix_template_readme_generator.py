import yaml
import sys
import os

def sanitize_description(text):
    return text.replace('\n', '<br>').replace('|', '\\|')

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

def extract_items(template):
    items = []
    for item in template.get('items', []):
        items.append({
            'name': item.get('name'),
            'key': item.get('key'),
            'type': item.get('type', ''),
            'units': item.get('units', ''),
            'description': item.get('description', '')
        })
    return items

def extract_macros(template):
    return template.get('macros', [])

def extract_triggers(template):
    triggers = []
    for item in template.get('items', []):
        for trigger in item.get('triggers', []):
            triggers.append({
                'name': trigger.get('name'),
                'expression': trigger.get('expression', ''),
                'priority': trigger.get('priority', ''),
                'description': trigger.get('description', '')
            })
    for trig in template.get('triggers', []):
        triggers.append({
            'name': trig.get('name'),
            'expression': trig.get('expression', ''),
            'priority': trig.get('priority', ''),
            'description': trig.get('description', '')
        })
    return triggers

def extract_discovery_rules(template):
    return template.get('discovery_rules', [])

def main():
    # Проверка аргументов
    if len(sys.argv) < 2:
        print("Использование: python script.py <template.yaml> [output.md]")
        sys.exit(1)
    template_path = sys.argv[1]
    if not os.path.exists(template_path):
        print(f"Файл {template_path} не найден.")
        sys.exit(1)
    # Имя md-файла по умолчанию
    output_md = sys.argv[2] if len(sys.argv) >= 3 else "README_template.md"

    data = load_template(template_path)
    templates = data.get('zabbix_export', {}).get('templates', [])
    md_output = ""
    for tpl in templates:
        md_output += f"# Template: {tpl.get('template', '')}\n\n"

        description = tpl.get('description', '').strip()
        if description:
            md_output += f"{description}\n\n"

        items = extract_items(tpl)
        if items:
            md_output += "## Items\n\n"
            headers = ["Name", "Key", "Type", "Units", "Description"]
            rows = [[i['name'], i['key'], str(i['type']), i['units'], i['description']] for i in items]
            md_output += markdown_table(headers, rows) + "\n\n"

        triggers = extract_triggers(tpl)
        if triggers:
            md_output += "## Triggers\n\n"
            headers = ["Name", "Expression", "Priority", "Description"]
            rows = [[t['name'], t['expression'], t['priority'], t['description']] for t in triggers]
            md_output += markdown_table(headers, rows) + "\n\n"

        macros = extract_macros(tpl)
        if macros:
            md_output += "## Macros\n\n"
            headers = ["Macro", "Value", "Description"]
            rows = [[m.get('macro', ''), m.get('value', ''), m.get('description', '')] for m in macros]
            md_output += markdown_table(headers, rows) + "\n\n"

        discovery_rules = extract_discovery_rules(tpl)
        if discovery_rules:
            md_output += "## Discovery rules\n\n"
            headers = ["Name", "Key", "Description"]
            rows = [[d.get('name', ''), d.get('key', ''), d.get('description', '')] for d in discovery_rules]
            md_output += markdown_table(headers, rows) + "\n\n"
            for dr in discovery_rules:
                item_protos = dr.get('item_prototypes', [])
                if item_protos:
                    md_output += f"### Item prototypes for discovery: {dr.get('name')}\n\n"
                    headers = ["Name", "Key", "Type", "Units", "Description"]
                    rows = [[ip.get('name', ''), ip.get('key', ''), str(ip.get('type', '')), ip.get('units', ''), ip.get('description', '')] for ip in item_protos]
                    md_output += markdown_table(headers, rows) + "\n\n"
                trigger_protos = dr.get('trigger_prototypes', [])
                if trigger_protos:
                    md_output += f"### Trigger prototypes for discovery: {dr.get('name')}\n\n"
                    headers = ["Name", "Expression", "Priority", "Description"]
                    rows = [[tp.get('name', ''), tp.get('expression', ''), tp.get('priority', ''), tp.get('description', '')] for tp in trigger_protos]
                    md_output += markdown_table(headers, rows) + "\n\n"
    # Запись в файл
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(md_output)
    print(f"Документация сохранена в {output_md}")

if __name__ == "__main__":
    main()
