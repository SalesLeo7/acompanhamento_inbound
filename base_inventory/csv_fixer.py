import csv
import io
import argparse

def fix_csv_formatting(input_path, output_path, reference_path=None):
    """
    Corrige problemas comuns de formatação em arquivos CSV, como aspas extras, 
    aspas duplicadas e desalinhamento de colunas.
    """
    target_col_count = None
    if reference_path:
        try:
            with open(reference_path, 'r', encoding='utf-8') as ref_f:
                ref_reader = csv.reader(ref_f)
                ref_row = next(ref_reader)
                target_col_count = len(ref_row)
            print(f"Número de colunas de referência do '{reference_path}': {target_col_count}")
        except Exception as e:
            print(f"Aviso: Não foi possível ler o arquivo de referência '{reference_path}': {e}")

    fixed_rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            
            # Remove aspas extras no início e fim da linha
            if line.startswith('"') and line.endswith('",'):
                line = line[1:-2]
            elif line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            
            # Corrige as aspas duplas internas ("" -> ")
            line = line.replace('""', '"')
            
            reader = csv.reader(io.StringIO(line))
            try:
                row = next(reader)
                
                if target_col_count is None and i == 0:
                    target_col_count = len(row)
                    print(f"Número de colunas inferido: {target_col_count}")

                if target_col_count is not None:
                    if len(row) > target_col_count:
                        if row[-1] == "":
                            row = row[:target_col_count]
                        else:
                            row = row[:target_col_count]
                    elif len(row) < target_col_count:
                        row.extend([""] * (target_col_count - len(row)))
                
                fixed_rows.append(row)
            except Exception as e:
                print(f"Erro na linha {i+1}: {e}")
                fixed_rows.append([line])

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(fixed_rows)
    print(f"Arquivo corrigido salvo em: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Corrige formatação de CSV.")
    parser.add_argument("input", help="Arquivo de entrada")
    parser.add_argument("output", help="Arquivo de saída")
    parser.add_argument("--reference", help="Arquivo de referência", default=None)
    args = parser.parse_args()
    fix_csv_formatting(args.input, args.output, args.reference)

if __name__ == "__main__":
    main()
