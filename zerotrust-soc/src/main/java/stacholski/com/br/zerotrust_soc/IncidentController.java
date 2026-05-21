package stacholski.com.br.zerotrust_soc;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/incidents")
public class IncidentController {

    @Autowired
    private IncidentRepository repository;

    @Value("${soc.security.api-key}")
    private String validApiKey;

    @PostMapping("/report")
    public ResponseEntity<String> receiveIncidentReport(
            @RequestHeader(value = "X-SOC-Token", required = false) String providedToken,
            @RequestBody Map<String, Object> payload) {

        // 1. BARREIRA ZERO-TRUST (Autenticação)
        if (providedToken == null || !providedToken.equals(validApiKey)) {
            System.out.println("\n[!] TENTATIVA DE INVASÃO BLOQUEADA: Token inválido ou ausente.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Acesso Negado: Falha de Identidade Zero-Trust.");
        }

        // 2. PERSISTÊNCIA (Salvar no Banco)
        Incident incident = new Incident();
        incident.setSource((String) payload.get("source"));
        incident.setAiReport((String) payload.get("ai_report"));
        repository.save(incident);

        // 3. LIMPEZA E FORMATAÇÃO DO TERMINAL (Limpa a tela usando ANSI)
        System.out.print("\033[H\033[2J");  
        System.out.flush();
        
        System.out.println("==================================================");
        System.out.println(" 🚨 ALERTA CRÍTICO REGISTRADO NO SOC CENTRAL 🚨 ");
        System.out.println("==================================================");
        System.out.println("ID no Banco : " + incident.getId());
        System.out.println("Data/Hora   : " + incident.getTimestamp());
        System.out.println("Origem      : " + incident.getSource());
        System.out.println("--------------------------------------------------");
        System.out.println("RELATÓRIO DA IA (Llama 3.2):");
        System.out.println(incident.getAiReport());
        System.out.println("==================================================\n");

        return ResponseEntity.ok("Incidente salvo e auditado no banco de dados.");
    }
}