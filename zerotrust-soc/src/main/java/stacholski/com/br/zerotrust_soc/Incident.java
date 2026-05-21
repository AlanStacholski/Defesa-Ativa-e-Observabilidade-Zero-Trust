package stacholski.com.br.zerotrust_soc;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
public class Incident {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String source;
    
    @Column(columnDefinition = "TEXT")
    private String aiReport;
    
    private LocalDateTime timestamp;

    public Incident() {
        this.timestamp = LocalDateTime.now();
    }

    // Getters e Setters
    public Long getId() { return id; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public String getAiReport() { return aiReport; }
    public void setAiReport(String aiReport) { this.aiReport = aiReport; }
    public LocalDateTime getTimestamp() { return timestamp; }
}