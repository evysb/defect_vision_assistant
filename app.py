import os
import shutil
import uuid
import pandas as pd
import gradio as gr
from datetime import datetime
from PIL import Image

# Importa módulos locais
from db import init_db, obter_todos_defeitos, executar_query_segura
from analysis import analyze_image, responder_consulta_defeitos, gerar_dashboard_matplotlib

# Inicializa o banco de dados e cria os diretórios necessários
init_db()
os.makedirs("./uploads", exist_ok=True)
os.makedirs("./temp", exist_ok=True)

# CSS Estilizado de Alta Performance para Manutenção Industrial (Light Theme)
CSS_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

:root, .dark {
    --body-background-fill: #f1f5f9 !important;
    --body-text-color: #1e293b !important;
    --background-fill-primary: #ffffff !important;
    --background-fill-secondary: #f8fafc !important;
    --border-color-primary: #e2e8f0 !important;
    --border-color-secondary: #cbd5e1 !important;
    --block-background-fill: #ffffff !important;
    --block-border-color: #e2e8f0 !important;
    --block-title-text-color: #0f172a !important;
    --block-label-text-color: #475569 !important;
    --input-background-fill: #ffffff !important;
    --input-border-color: #e2e8f0 !important;
    --input-text-color: #0f172a !important;
    --table-border-color: #e2e8f0 !important;
    --table-even-background-fill: #f8fafc !important;
    --table-row-focus: #f1f5f9 !important;
}

body, .dark body {
    background-color: #f1f5f9 !important;
    color: #1e293b !important;
}
.gradio-container, .dark .gradio-container {
    background: linear-gradient(135deg, #ffffff, #f8fafc) !important;
    max-width: 1200px !important;
    border-radius: 20px !important;
    border: 1px solid rgba(0, 0, 0, 0.06) !important;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.06) !important;
    font-family: 'Outfit', sans-serif !important;
    padding: 20px !important;
}
.tab-nav, .dark .tab-nav {
    border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
    margin-bottom: 25px !important;
}
.tab-nav button, .dark .tab-nav button {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #64748b !important;
    border-bottom: 3px solid transparent !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
}
.tab-nav button.selected, .dark .tab-nav button.selected {
    color: #2563eb !important;
    border-bottom: 3px solid #2563eb !important;
    background: transparent !important;
}
.primary-btn, .dark .primary-btn {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.primary-btn:hover, .dark .primary-btn:hover {
    background: linear-gradient(135deg, #60a5fa, #3b82f6) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.2) !important;
}
.danger-btn, .dark .danger-btn {
    background: linear-gradient(135deg, #ef4444, #dc2626) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    transition: all 0.25s ease !important;
}
.danger-btn:hover, .dark .danger-btn:hover {
    background: linear-gradient(135deg, #f87171, #ef4444) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(220, 38, 38, 0.2) !important;
}
.critico-banner, .dark .critico-banner {
    background: linear-gradient(135deg, #fef2f2, #fee2e2) !important;
    border: 2px solid #ef4444 !important;
    color: #991b1b !important;
    border-radius: 12px !important;
    padding: 15px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.15) !important;
    animation: pulse-red 2s infinite alternate !important;
}
@keyframes pulse-red {
    0% {
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.1);
        border-color: #fca5a5;
    }
    100% {
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.3);
        border-color: #ef4444;
    }
}
/* Cards do Histórico de Defeitos */
.defect-grid, .dark .defect-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
    padding: 10px 0;
}
.defect-card, .dark .defect-card {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: 14px;
    display: flex;
    overflow: hidden;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.defect-card:hover, .dark .defect-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 16px 28px rgba(0, 0, 0, 0.08) !important;
    border-color: rgba(37, 99, 235, 0.3) !important;
    background: #ffffff !important;
}
.card-left, .dark .card-left {
    width: 110px;
    min-width: 110px;
    background: rgba(0, 0, 0, 0.02) !important;
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
}
.defect-thumb {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.defect-no-img, .dark .defect-no-img {
    color: #64748b !important;
    font-size: 12px;
    text-align: center;
    padding: 10px;
}
.card-right, .dark .card-right {
    padding: 14px;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
    gap: 8px;
}
.card-header-row h3, .dark .card-header-row h3 {
    margin: 0;
    font-size: 15px;
    font-weight: 700;
    color: #0f172a !important;
}
.badge {
    font-size: 9px;
    padding: 3px 8px;
    border-radius: 10px;
    font-weight: 800;
    white-space: nowrap;
}
.badge-critico, .dark .badge-critico {
    background-color: rgba(239, 68, 68, 0.1) !important;
    color: #dc2626 !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
}
.badge-alto, .dark .badge-alto {
    background-color: rgba(249, 115, 22, 0.1) !important;
    color: #ea580c !important;
    border: 1px solid rgba(249, 115, 22, 0.3) !important;
}
.badge-medio, .dark .badge-medio {
    background-color: rgba(234, 179, 8, 0.1) !important;
    color: #ca8a04 !important;
    border: 1px solid rgba(234, 179, 8, 0.3) !important;
}
.badge-baixo, .dark .badge-baixo {
    background-color: rgba(16, 185, 129, 0.1) !important;
    color: #059669 !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
}
.card-body-row, .dark .card-body-row {
    font-size: 12px;
    color: #475569 !important;
    margin: 3px 0;
}
.card-details, .dark .card-details {
    margin-top: 8px;
    font-size: 11px;
    background: rgba(0, 0, 0, 0.02) !important;
    border-radius: 6px;
    padding: 6px;
    border: 1px solid rgba(0, 0, 0, 0.04) !important;
}
.card-details summary, .dark .card-details summary {
    cursor: pointer;
    font-weight: 600;
    color: #2563eb !important;
    outline: none;
}
.card-details p, .dark .card-details p {
    color: #334155 !important;
    margin: 4px 0;
}
"""

def get_thumbnail_base64(caminho_imagem: str) -> str:
    """Converte a imagem em miniatura Base64 para renderização inline rápida na galeria."""
    if not caminho_imagem or not os.path.exists(caminho_imagem):
        return ""
    try:
        from io import BytesIO
        import base64
        with Image.open(caminho_imagem) as img:
            img = img.convert("RGB")
            img.thumbnail((120, 120))
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=80)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"Erro ao gerar miniatura: {e}")
        return ""

def render_historico_html() -> str:
    """Gera o HTML para a galeria de cards de inspeções anteriores."""
    try:
        defeitos = obter_todos_defeitos()
    except Exception as e:
        return f"<p style='color: #dc2626;'>Erro ao ler histórico: {str(e)}</p>"
        
    if not defeitos:
        return """
        <div style='text-align: center; padding: 40px; color: #64748b;'>
            <p style='font-size: 18px;'>📭 Nenhuma inspeção registrada.</p>
            <p style='font-size: 14px;'>Envie uma foto de peça na aba "Inspeção Visual" para iniciar.</p>
        </div>
        """
        
    html_cards = []
    for d in defeitos:
        thumb = get_thumbnail_base64(d["imagem_path"])
        img_tag = f'<img src="{thumb}" class="defect-thumb" />' if thumb else '<div class="defect-no-img">Sem Foto</div>'
        
        # Badge de severidade estilizado
        sev = d["severidade"].upper()
        if "CRÍTICO" in sev or "CRITICO" in sev:
            badge_class = "badge-critico"
        elif "ALTO" in sev:
            badge_class = "badge-alto"
        elif "MÉDIO" in sev or "MEDIO" in sev:
            badge_class = "badge-medio"
        else:
            badge_class = "badge-baixo"
            
        # Formatar data
        data_registro = d["data"]
        try:
            # Tenta converter ISO-8601
            if "T" in data_registro:
                dt = datetime.fromisoformat(data_registro)
            else:
                dt = datetime.strptime(data_registro, "%Y-%m-%d %H:%M:%S")
            data_formatada = dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            data_formatada = data_registro
            
        card = f"""
        <div class="defect-card">
            <div class="card-left">
                {img_tag}
            </div>
            <div class="card-right">
                <div class="card-header-row">
                    <h3>{d["tipo"]}</h3>
                    <span class="badge {badge_class}">{sev}</span>
                </div>
                <div class="card-body-row">📅 {data_formatada}</div>
                <div class="card-body-row">📍 {d["localizacao"]}</div>
                <details class="card-details">
                    <summary>Ver Detalhes do Defeito</summary>
                    <p><strong>Causa Raiz:</strong> {d["causa"] or "Não informada"}</p>
                    <p style="color: #2563eb;"><strong>Ação Corretiva:</strong> {d["acao"] or "Nenhuma recomendada"}</p>
                    <p style="font-size: 9px; color: #64748b; margin-top: 6px;">ID: {d["id"]}</p>
                </details>
            </div>
        </div>
        """
        html_cards.append(card)
        
    grid_content = "".join(html_cards)
    return f'<div class="defect-grid">{grid_content}</div>'

def processar_inspecao(imagem_path: str, backend: str):
    """
    Executa a análise da imagem, salvando automaticamente no banco,
    e retorna a resposta estruturada exigida.
    """
    if not imagem_path:
        return (
            "⚠️ Por favor, envie uma foto antes de iniciar a inspeção.",
            gr.update(visible=False),
            gr.update(),
            gr.update()
        )
        
    try:
        usar_simulador = (backend == "Simulador Local (Offline)")
        
        # Mover imagem do temporário do Gradio para a pasta permanente
        ext = os.path.splitext(imagem_path)[1] or ".jpg"
        filename = f"inspecao_{uuid.uuid4().hex}{ext}"
        caminho_permanente = os.path.join("uploads", filename)
        shutil.copy(imagem_path, caminho_permanente)
        
        # Chama o analisador (ele já salva no SQLite de forma automática)
        dados = analyze_image(caminho_permanente, usar_simulador=usar_simulador)
        
        # Formatar a data/hora do registro
        data_registro_str = dados.get("data_registro", "")
        try:
            dt = datetime.fromisoformat(data_registro_str)
            data_formatada = dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            data_formatada = data_registro_str
            
        sev = dados.get("severidade", "BAIXO").upper()
        
        # Formata o Output Padrão da Análise Visual
        resultado_md = (
            f"⚠️ SEVERIDADE: {sev}\n\n"
            f"**Defeito identificado:** {dados.get('tipo_defeito')}\n"
            f"**Localização:** {dados.get('localizacao')}\n"
            f"**Causa provável:** {dados.get('causa_provavel')}\n"
            f"**Ação recomendada:** {dados.get('acao_recomendada')}\n\n"
            f"✅ Registro salvo — ID: {dados.get('id_inspecao')} | {data_formatada}"
        )
        
        # Tratamento especial se a severidade for CRÍTICO (Aviso destacado - Regra de Comportamento 4)
        is_critico = "CRÍTICO" in sev or "CRITICO" in sev
        if is_critico:
            aviso_critico = "🚨 **ALERTA CRÍTICO:** Risco de falha imediata do componente ou comprometimento da segurança operacional! Isolamento de área e ação corretiva imediata são mandatórios."
            resultado_md = f"{aviso_critico}\n\n---\n\n{resultado_md}"
            banner_update = gr.update(value=aviso_critico, visible=True)
        else:
            banner_update = gr.update(value="", visible=False)
            
        # Atualiza a galeria e o dashboard
        historico_novo = render_historico_html()
        dashboard_novo = gerar_dashboard_matplotlib()
        
        return resultado_md, banner_update, historico_novo, dashboard_novo
        
    except Exception as e:
        erro_msg = f"❌ **Erro no processamento da inspeção:** {str(e)}"
        return erro_msg, gr.update(visible=False), gr.update(), gr.update()

def processar_consulta(pergunta: str):
    """Processa a consulta NL, gera a tabela de dados estruturada e atualiza o CSV de exportação."""
    resposta_texto, df_dados = responder_consulta_defeitos(pergunta)
    
    # Converte os resultados para um DataFrame do Pandas para exibição no Gradio Dataframe
    if df_dados:
        df = pd.DataFrame(df_dados)
    else:
        df = pd.DataFrame(columns=["ID", "Data", "Tipo de Defeito", "Localização", "Severidade", "Ação Recomendada"])
        
    # Salva em arquivo CSV temporário se tiver linhas
    csv_file = None
    if not df.empty:
        try:
            csv_path = os.path.join("temp", "resultado_inspecao.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            csv_file = csv_path
        except Exception as e:
            print(f"Erro ao salvar CSV: {e}")
            
    file_update = gr.update(value=csv_file, visible=(csv_file is not None))
    
    return resposta_texto, df, file_update

# Criação da Interface Gradio
with gr.Blocks(title="Assistente de Manutenção Industrial") as interface:
    
    # Título Principal do Painel
    gr.HTML("""
    <div style='text-align: center; margin-bottom: 25px; border-bottom: 1px solid rgba(0,0,0,0.06); padding-bottom: 15px;'>
        <h1 style='font-size: 30px; font-weight: 800; color: #0f172a; margin-bottom: 5px; letter-spacing: -0.5px;'>
            🛠️ DefectVision Industrial Assistant
        </h1>
        <p style='color: #475569; font-size: 15px; margin: 0;'>
            Inspeção visual automatizada de peças e consulta de histórico em linguagem natural via IA
        </p>
    </div>
    """)
    
    with gr.Tabs() as abas:
        
        # --- ABA 1: INSPEÇÃO VISUAL ---
        with gr.Tab("Inspeção Visual", id="aba_inspecao"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📸 1. Capturar ou Carregar Imagem da Peça")
                    imagem_input = gr.Image(
                        label="Imagem do Equipamento/Peça", 
                        type="filepath", 
                        sources=["upload", "webcam"]
                    )
                    
                    backend_select = gr.Radio(
                        choices=["Hugging Face BLIP-large (Local)", "Simulador Local (Offline)"],
                        value="Hugging Face BLIP-large (Local)",
                        label="Modelo de Análise Visual"
                    )
                    
                    btn_analisar = gr.Button("🔍 Iniciar Inspeção Técnica", elem_classes="primary-btn")
                    
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 2. Relatório do Diagnóstico")
                    
                    # Banner animado para Alertas Críticos
                    aviso_critico_box = gr.Markdown(
                        "", 
                        elem_classes="critico-banner", 
                        visible=False
                    )
                    
                    # Relatório de Diagnóstico Estruturado
                    relatorio_output = gr.Markdown(
                        "*Aguardando envio de peça e ativação da inspeção...*",
                        line_breaks=True
                    )
                    
        # --- ABA 2: CONSULTA DE HISTÓRICO ---
        with gr.Tab("Consulta de Histórico", id="aba_consulta"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 💬 Perguntar ao Histórico de Manutenção")
                    txt_pergunta = gr.Textbox(
                        label="Descreva sua busca por registros de inspeção",
                        placeholder="Ex: defeitos críticos do mês passado ou todos os registros de ferrugem",
                        lines=3
                    )
                    btn_consultar = gr.Button("🔎 Enviar Consulta", elem_classes="primary-btn")
                    
                    gr.Markdown("💡 **Exemplos de consultas válidas:**\n"
                                "- *\"defeitos críticos do mês passado\"*\n"
                                "- *\"todos os registros de ferrugem\"*\n"
                                "- *\"quantas inspeções esta semana\"*\n"
                                "- *\"peças com severidade alta em junho\"*")
                    
                with gr.Column(scale=2):
                    gr.Markdown("### 🤖 Diagnóstico do Histórico")
                    consulta_resumo = gr.Markdown("*Aguardando consulta...*")
                    
                    gr.Markdown("### 📋 Registros Encontrados")
                    df_resultados = gr.Dataframe(
                        headers=["ID", "Data", "Tipo de Defeito", "Localização", "Severidade", "Ação Recomendada"],
                        datatype=["str", "str", "str", "str", "str", "str"],
                        interactive=False
                    )
                    
                    # Componente para download do CSV resultante
                    csv_download = gr.File(
                        label="📥 Exportar Resultados (CSV)", 
                        visible=False
                    )
                    
        # --- ABA 3: PAINEL E GALERIA ---
        with gr.Tab("Indicadores e Galeria", id="aba_galeria"):
            gr.Markdown("### 📊 Indicadores Gerais de Manutenção")
            # Exibe o gráfico do dashboard gerado dinamicamente
            dashboard_img = gr.Image(
                value=gerar_dashboard_matplotlib(),
                label="Estatísticas de Ocorrências",
                interactive=False
            )
            
            gr.Markdown("### 📁 Histórico Geral de Peças Inspecionadas")
            galeria_html = gr.HTML(value=render_historico_html())
            
    # Conexão de Eventos (Triggers)
    btn_analisar.click(
        fn=processar_inspecao,
        inputs=[imagem_input, backend_select],
        outputs=[relatorio_output, aviso_critico_box, galeria_html, dashboard_img]
    )
    
    btn_consultar.click(
        fn=processar_consulta,
        inputs=[txt_pergunta],
        outputs=[consulta_resumo, df_resultados, csv_download]
    )

# Execução local da aplicação
if __name__ == "__main__":
    interface.launch(server_name="127.0.0.1", server_port=7861, share=False, css=CSS_STYLE)
